#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 13:57:31 2023

@author: sweav
"""
import itertools
import math
from math import ceil
from math import prod as product

import numpy as np
import pandas as pd
from numpy import polyfit
from pymatgen.analysis.local_env import CrystalNN
from scipy.interpolate import RegularGridInterpolator
from scipy.spatial import ConvexHull
from scipy.signal import savgol_filter
from simmate.toolkit import Structure


"""
This module defines functions that are used in the warren lab badelf
algorithm. There are general types of functions:
    1. Miscellaneous functions used in several parts of the algorithm
    2. Functions used during partitioning
    3. Functions used when assigning voxels. This is further split as follows.
        a. Functions for assigning voxels away from planes
        b. Functions for assigning voxels split by one plane
        c. Functions for assigning voxels split by multiple planes
        d. Functions for assigning remaining voxels
"""


###############################################################################
# This section defines functions that are used in various locations throughout
# the algorithm. They are mostly conversions between fractional, voxel, and
# cartesian/real coordinates.
###############################################################################


def get_voxel_from_index(site, lattice):
    """
    This function takes in a fractional coordinate and returns the index for
    the equivalent voxel.

    VASP voxel indices go from 1 to grid_size along each axis. (e.g., 1 to 70)
    Fractional coordinates go from 0 to 1 along each axis.

    Fractional coordinate (0,0,0) corresponds to the center
    of voxel (1,1,1).
    Fractional coordinate (1,1,1) cooresponds to the center
    of voxel (grid_size_a, grid_size_b, grid_size_c).

    This code maintains the VASP standards throughout.

    """

    grid_size = lattice["grid_size"]
    frac = lattice["coords"][site]
    voxel_pos = [a * b + 1 for a, b in zip(grid_size, frac)]
    # voxel positions go from 1 to (grid_size + 0.9999)
    return np.array(voxel_pos)


def get_voxel_from_neigh_CrystalNN(neigh, lattice):
    """
    Gets the voxel coordinate from a neighbor atom object from CrystalNN or
    VoronoiNN
    """
    grid_size = lattice["grid_size"]
    frac = neigh["site"].frac_coords
    voxel_pos = [a * b + 1 for a, b in zip(grid_size, frac)]
    # voxel positions go from 1 to (grid_size + 0.9999)
    return np.array(voxel_pos)


def get_voxel_from_neigh(neigh, lattice):
    """
    Gets the voxel coordinate from a neighbor atom object from CrystalNN or
    VoronoiNN
    """
    grid_size = lattice["grid_size"]
    frac = neigh.frac_coords
    voxel_pos = [a * b + 1 for a, b in zip(grid_size, frac)]
    # voxel positions go from 1 to (grid_size + 0.9999)
    return np.array(voxel_pos)


def get_frac_from_vox(voxel_position: list, lattice: dict):
    """
    Function that takes in a voxel position and returns the fractional
    coordinates.
    """
    size = lattice["grid_size"]
    fa, fb, fc = [((a - 1) / b) for a, b in zip(voxel_position, size)]
    coords = np.array([fa, fb, fc])
    return coords


def get_real_from_frac(frac_pos, lattice):
    """
    Function that takes in fractional coordinates and returns real coordinates
    """
    fa, fb, fc = frac_pos[0], frac_pos[1], frac_pos[2]
    a, b, c = lattice["a"], lattice["b"], lattice["c"]
    x = fa * a[0] + fb * b[0] + fc * c[0]
    y = fa * a[1] + fb * b[1] + fc * c[1]
    z = fa * a[2] + fb * b[2] + fc * c[2]
    coords = np.array([x, y, z])
    return coords


def get_real_from_vox(voxel_position: list, lattice: dict):
    """
    We need to turn voxel_position this into a real space position.
    First, to get fractional positions, we follow the VASP notation and
    subtract 1 from pos_vox, then divide by the grid_size.
    The rest is just standard geometry to get the x,y,z real-space positions.
    """
    frac_pos = get_frac_from_vox(voxel_position, lattice)
    coords = get_real_from_frac(frac_pos, lattice)
    return coords


def get_number_of_partitions(
    df,
    nworkers,
):
    """
    Gets the number of partitions a Dask dataframe should have in this algorithm.
    """
    # We need the total number of voxels so that we can make sure our partitions
    # aren't too large. I did some light testing and found that 128000 was a
    # good limit for the number of voxels that could be handled by a worker
    # with 2GB of memory. Much larger and it could start having issues.
    total_voxels = len(df)
    if total_voxels <= 128000 * nworkers:
        npartitions = nworkers
    elif total_voxels > 128000 * nworkers:
        npartitions = math.ceil(total_voxels / 128000)
    return npartitions


###############################################################################
# This section defines functions that are used for partitioning a unit cell
# based on the ELF (or possibly the charge density). This includes functions that
# read in the POSCAR, ELFCAR and CHGCAR into arrays, find nearest and voronoi
# neighbors for each atom, finds the minimum of an interpolated line drawn
# between each atom pair, and finds the plane point and plane vector associated
# with the plane dividing these atoms at this point.
###############################################################################
def get_lattice(partition_file: str):
    """
    This function gets several important things from the lattice defined in
    the partitioning file
    """
    lattice = {}
    lattice["coords"] = []
    lattice["num_atoms"] = 1000

    with open(partition_file) as f:
        for i, line in enumerate(f):
            if i == 2:
                lattice["a"] = [float(x) for x in line.split()]
            if i == 3:
                lattice["b"] = [float(x) for x in line.split()]
            if i == 4:
                lattice["c"] = [float(x) for x in line.split()]
            if i == 5:
                lattice["elements"] = line.split()
            if i == 6:
                lattice["num_atoms"] = sum([int(x) for x in line.split()])
                lattice["elements_num"] = [int(x) for x in line.split()]
            if 8 <= i < 8 + lattice["num_atoms"]:
                lattice["coords"].append([float(x) for x in line.split()])
            if i == 9 + lattice["num_atoms"]:
                lattice["grid_size"] = [int(x) for x in line.split()]
            if i == 10 + lattice["num_atoms"]:
                lattice["volume"] = np.dot(
                    np.cross(lattice["a"], lattice["b"]), lattice["c"]
                )
                lattice["lines"] = ceil(product(lattice["grid_size"]) / 10)
                break
    return lattice


def get_closest_neighbors(structure: Structure):
    """
    Function for getting the closest neighbors
    """
    c = CrystalNN(search_cutoff=5)
    closest_neighbors = {}
    for i in range(len(structure)):
        _, _, d = c.get_nn_data(structure, n=i)
        biggest = max(d)
        closest_neighbors[i] = d[biggest]
    return closest_neighbors


def get_50_neighbors(structure):
    """
    Function for getting the 50 closest neighbors. This is necessary for partitioning
    because the CrystalNN function from pymatgen will not necessarily find the
    correct set of atoms needed to create a full partitioning set.
    """
    # Get all possible neighbor atoms for each atom within 15 angstroms
    all_neighbors = structure.get_all_neighbors(15)
    neighbors50 = []
    # For each atom, create a df to store the neighbor and its distance
    # from the atom. Then sort this df by distance and only keep the
    # 50 closest neighbors
    for site, neighs in enumerate(all_neighbors):
        site_df = pd.DataFrame(columns=["neighbor", "distance"])
        site_object = structure[site]
        for neigh in neighs:
            # get distance
            distance = math.dist(neigh.coords, site_object.coords)
            # add neighbor, distance pair to df
            site_df.loc[len(site_df)] = [neigh, distance]
        # sort by distance and truncate to first 50
        site_df = site_df.sort_values(by="distance")
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Temporarily switching to 50 nearest planes
        site_df = site_df.iloc[0:50]
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Add the neighbors as a list to the df
        neighbors50.append(site_df["neighbor"].to_list())
    return neighbors50


def get_grid_axes(grid):
    """
    Gets the the possible indices for each dimension of a padded grid.
    e.g. if the original charge density grid is 20x20x20, this function will
    return three arrays with integers from 0 to 21.
    """
    a = np.linspace(0, grid.shape[0] + 1, grid.shape[0] + 2)
    b = np.linspace(0, grid.shape[1] + 1, grid.shape[1] + 2)
    c = np.linspace(0, grid.shape[2] + 1, grid.shape[2] + 2)
    return a, b, c


def get_grid_axes_large_pad(grid, size):
    """
    Gets the the possible indices for each dimension of a padded grid.
    e.g. if the original charge density grid is 20x20x20, this function will
    return three arrays with integers from 0 to 21.
    """
    a = np.linspace(0, grid.shape[0] + (size - 1) * 2 + 1, grid.shape[0] + size * 2)
    b = np.linspace(0, grid.shape[1] + (size - 1) * 2 + 1, grid.shape[1] + size * 2)
    c = np.linspace(0, grid.shape[2] + (size - 1) * 2 + 1, grid.shape[2] + size * 2)
    return a, b, c


def get_partitioning_grid(
    partition_file: str,
    lattice: dict,
):
    """
    Loads in the partitioning file (usualy ELFCAR) into a 3D numpy array
    """
    try:
        grid = np.loadtxt(
            partition_file,
            skiprows=10 + lattice["num_atoms"],
            max_rows=lattice["lines"],
        ).ravel()
    except:
        grid1 = np.loadtxt(
            partition_file,
            skiprows=10 + lattice["num_atoms"],
            max_rows=lattice["lines"] - 1,
        ).ravel()
        grid2 = np.loadtxt(
            partition_file,
            skiprows=10 + lattice["num_atoms"] + lattice["lines"] - 1,
            max_rows=1,
        ).ravel()
        grid = np.concatenate((grid1, grid2))

    grid = grid.ravel().reshape(lattice["grid_size"], order="F")
    return grid


def get_charge_density_grid(
    charge_file: str,
    lattice: dict,
):
    """
    Loads the charge density from the charge file (CHGCAR) into a 3D numpy array
    """
    try:
        chg1 = np.loadtxt(
            charge_file,
            skiprows=10 + lattice["num_atoms"],
            max_rows=lattice["lines"] * 2 - 1,
        ).ravel()
        chg2 = np.loadtxt(
            charge_file,
            skiprows=10 + lattice["num_atoms"] + lattice["lines"] * 2 - 1,
            max_rows=1,
        ).ravel()
        chg = np.concatenate((chg1, chg2))
    except:
        chg1 = np.loadtxt(
            charge_file,
            skiprows=10 + lattice["num_atoms"],
            max_rows=lattice["lines"] * 2 - 2,
        ).ravel()
        chg2 = np.loadtxt(
            charge_file,
            skiprows=10 + lattice["num_atoms"] + lattice["lines"] * 2 - 2,
            max_rows=1,
        ).ravel()
        chg = np.concatenate((chg1, chg2))

    chg = chg.reshape(lattice["grid_size"], order="F")
    return chg


def get_partitioning_line_rough(site_pos, neigh_pos, grid):
    """
    Finds a line of voxel positions between two atom sites and then finds the value
    of the partitioning grid at each of these positions. The values are found
    using an interpolation function defined using SciPy's RegularGridInterpeter
    using the 'cubic' method.
    """
    steps = 200
    slope = [b - a for a, b in zip(site_pos, neigh_pos)]
    slope_increment = [float(x) / steps for x in slope]

    # get a list of points along the connecting line
    position = site_pos
    line = [position]
    for i in range(steps):
        # move position by slope_increment
        position = [float(a + b) for a, b in zip(position, slope_increment)]

        # Wrap values back into cell
        # We must do (a-1) to shift the voxel index (1 to grid_max+1) onto a
        # normal grid, (0 to grid_max), then do the wrapping function (%), then
        # shift back onto the VASP voxel index.
        position = [
            round((float(((a - 1) % b) + 1)), 12) for a, b in zip(position, grid.shape)
        ]

        line.append(position)

    # The partitioning uses a padded grid and grid interpolation to find the
    # location of dividing planes.
    padded = np.pad(grid, 1, mode="wrap")

    # interpolate grid to find values that lie between voxels. This is done
    # with a cruder interpolation here and then the area close to the minimum
    # is examened more closely with a more rigorous interpolation in
    # get_line_frac_min
    a, b, c = get_grid_axes(grid)
    fn = RegularGridInterpolator((a, b, c), padded, method="linear")
    # get a list of the ELF values along the line
    values = []

    for pos in line:
        adjusted_pos = [x for x in pos]
        value = float(fn(adjusted_pos))
        values.append(value)
    return line, values

def find_minimum(values):
    """
    Finds the local minima in a list of values and returns the index and value
    at each as a list of form [[min_index1, min_value1], [min_index2, min_value2], ...]
    """
    minima = [
        [i, y]
        for i, y in enumerate(values)
        if ((i == 0) or (values[i - 1] >= y))
        and ((i == len(values) - 1) or (y < values[i + 1]))
    ]
    return minima

def find_maximum(values):
    """
    Finds the local maxima in a list of values and returns the index and value
    at each as a list of form [[max_index1, max_value1], [max_index2, max_value2], ...]
    """
    maxima = [
        [i,y]
        for i, y in enumerate(values)
        if ((i == 0) or (values[i - 1] <= y))
        and ((i == len(values) - 1) or (y > values[i + 1])) 
        ]
    return maxima

def get_closest_extrema_to_center(values, extrema):
    """
    Takes a list of values and the relative extrema (either minima or maxima)
    and finds which extrema is closest to the center of the line.
    """
    midpoint = len(values) / 2
    differences = []
    for pos, val in extrema:
        diff = abs(pos - midpoint)
        differences.append(diff)
    min_pos = differences.index(min(differences))
    global_extrema = extrema[min_pos]
    return global_extrema

def check_bond_for_covalency(values: list):
    """
    Checks for covalent/metallic behavior along a bond. This is done by comparing 
    the closest local maximum and minimum to the center of the bond. If the
    maximum is closer, the bond is considered to have some covalent behavior.
    """
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # In the future, these covalent areas should also be assigned sites so that
    # covalent electrides can be handled as well. There is also probably a more
    # rigorous point to compare to than the center of the bond depending on the
    # sizes of the atoms. Maybe compare the ratio of atomic radii and set the
    # comparison point further from the larger atom based on this ratio?
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # get the center of the ELF line
    midpoint = len(values) / 2
    
    # minima function gives all local minima along the values
    minima = find_minimum(values)
    maxima = find_maximum(values)

    # then we grab the local minima closest to the midpoint of the values
    global_min = get_closest_extrema_to_center(values, minima)
    global_max = get_closest_extrema_to_center(values, maxima)
    
    # get the distance from the minimum and maximum to the center. The position 
    # of the extrema is stored in the first index of the extrema list
    min_dist = abs(midpoint-global_min[0])
    max_dist = abs(midpoint-global_max[0])
    
    # get the ELF values at the minimum and maximum. This is stored in the
    # second index of the extrema list
    min_elf = global_min[1]
    max_elf = global_max[1]
    
    # If the maximum is closer to the center of the line than the minimum, then
    # we consider this bond to have metallic or covalent behavior and return True
    if min_dist > max_dist:
        return True
    
    # If the minimum is closer we need to do an extra check. If the minimum has
    # a value that is over half the value of the maximum, it is likely that there
    # are two local maxima that are close to the center of the bond, which we
    # also view as covalent and return as True. If it is less than half the 
    # value of the maximum, this bond is not strongly covalent and the partitioning
    # will work, so we return False.
    if min_dist <= max_dist:
        if min_elf > max_elf/2:
            return True
        else:
            return False
        
def get_line_frac_min_rough(values, rough_partitioning=False):
    """
    Finds the minimum point of a list of values along a line, then returns the
    fractional position of this values position along the line.
    """
    # minima function gives all local minima along the values
    minima = find_minimum(values)
    # maxima = find_maximum(values)

    # then we grab the local minima closest to the midpoint of the values
    global_min = get_closest_extrema_to_center(values, minima)
    # global_max = get_closest_extrema_to_center(values, maxima)
       
    # If we have a high enough voxel resolution we only want to run the rough
    # interpolation. If that's the case we want to do a polynomial fit here
    # to ensure that we have the correct position
    if rough_partitioning:
        # Get the section of the line surrounding the minimum to perform a fit
        poly_line_section = values[global_min[0] - 3 : global_min[0] + 4]
        poly_line_x = [i for i in range(global_min[0] - 3, global_min[0] + 4)]
        # get the polynomial fit
        try:
            a, b, c = polyfit(poly_line_x, poly_line_section, 2)
            # find the minimum and change the values of the global_min list
            x = -b / (2 * a)
            global_min[0] = x
            global_min[1] = np.polyval(np.array([a, b, c]), x)
        except:
            pass

    global_min.append(global_min[0] / (len(values) - 1))
    return global_min


def get_line_frac_min_fine(elf_pos, elf_min_index, grid):
    # We need more padding for the more rigorous interpolation to get the same
    # results.
    amount_to_pad = 10

    padded = np.pad(grid, amount_to_pad, mode="wrap")

    # interpolate the grid with a more rigorous method to find more exact value
    # for the plane.
    a, b, c = get_grid_axes_large_pad(grid, amount_to_pad)
    fn = RegularGridInterpolator((a, b, c), padded, method="cubic")

    # create variables for if the line needs to be shifted from what the
    # rough partitioning found
    centered = False
    amount_to_shift = 0
    attempts = 0

    try:
        while centered == False:
            if attempts == 5:
                raise Exception()
            else:
                attempts += 1
            # If the position wasn't centered previously, we need to shift
            # the index
            elf_min_index = elf_min_index + amount_to_shift
            line_section = elf_pos[elf_min_index - 3 : elf_min_index + 4]
            line_section_x = [i for i in range(elf_min_index - 3, elf_min_index + 4)]

            values_fine = []
            # Get the list of values from the interpolated grid
            for pos in line_section:
                new_pos = [i + amount_to_pad - 1 for i in pos]
                value_fine = float(fn(new_pos))
                values_fine.append(value_fine)

            # Find the minimum value of this line as well as the index for this value's
            # position.
            minimum_value = min(values_fine)
            min_pos = values_fine.index(minimum_value)

            if min_pos == 4:
                # Our line is centered and we can move on
                centered = True
            else:
                # Our line is not centered and we need to adjust it
                amount_to_shift = min_pos - 4


    except:
        # The above sometimes fails because the linear fitting gives a guess
        # for the minimum that isn't close. To handle this we treat these
        # situations rigorously
        values = []

        # Get the ELF value for every position in the line.
        for pos in elf_pos:
            new_pos = [i + amount_to_pad - 1 for i in pos]
            value = float(fn(new_pos))
            values.append(value)

        # Get a list of all of the minima along the line
        minima = find_minimum(values)

        # then we grab the local minima closest to the midpoint of the line
        global_min = get_closest_extrema_to_center(values, minima)

        # now we want a small section of the line surrounding the minimum
        values_fine = values[global_min[0] - 3 : global_min[0] + 4]
        line_section_x = [i for i in range(global_min[0] - 3, global_min[0] + 4)]

    # now that we've found the values surrounding the minimum of our line,
    # we can fit these values to a 2nd degree polynomial and solve for its
    # minimum point
    try:
        d, e, f = polyfit(line_section_x, values_fine, 2)
    except:
        pass
    x = -e / (2 * d)
    elf_min_index_new = x
    elf_min_value_new = np.polyval(np.array([d, e, f]), x)

    # Get the position along the line as a fraction
    elf_min_frac_new = elf_min_index_new / (len(elf_pos) - 1)
    return elf_min_index_new, elf_min_value_new, elf_min_frac_new


def get_position_from_min(elf_min_frac, site_pos, neigh_pos):
    """
    Gives the voxel position/coords for the minimum along a partitioning line
    between two atoms. The minimum point is where the dividing plane should lie.
    """
    # get the vector that points between the site and its neighbor (in vox  coords)
    difference = [b - a for a, b in zip(site_pos, neigh_pos)]
    # get the vector that points from the site to the global_min
    min_pos = [x * elf_min_frac for x in difference]
    # add the vector components of the site and minimum point together to get
    # the vector pointing directly to the minimum
    min_pos = [(a + b) for a, b in zip(min_pos, site_pos)]
    return np.array(min_pos)


def get_unit_vector(site_pos, neigh_pos, lattice):
    """
    Gets the unit vector pointing in the direction between two atom sites
    """
    # get the positions of the atoms in cartesian coordinates.
    real_site_pos = get_real_from_vox(site_pos, lattice)
    real_neigh_pos = get_real_from_vox(neigh_pos, lattice)
    # The equation of a plane passing through (x1,y1,z1) with normal vector
    # [a,b,c] is:
    #     a(x-x1) + b(y-y1) + c(z-z1) = 0
    # we want the normal vector to be unit vector because later on we
    # will use this information to get the distance of a voxel from
    # the plane.
    normal_vector = [(b - a) for a, b in zip(real_site_pos, real_neigh_pos)]
    unit_vector = [(x / np.linalg.norm(normal_vector)) for x in normal_vector]
    return np.array(unit_vector)


def get_plane_sign(point, unit_vector, site_pos, lattice):
    """
    Gets the sign associated with a point compared with a plane. This should
    be negative for an atoms position compared with a plane dividing it from
    other atoms.
    """
    # get all of the points in cartesian coordinates
    x, y, z = get_real_from_vox(site_pos, lattice)
    a, b, c = unit_vector
    x1, y1, z1 = point
    value_of_plane_equation = a * (x - x1) + b * (y - y1) + c * (z - z1)
    # get the distance of the point from the plane with some allowance of error.
    if value_of_plane_equation > 1e-6:
        return "positive", abs(value_of_plane_equation)
    elif value_of_plane_equation < -1e-6:
        return "negative", abs(value_of_plane_equation)
    else:
        return "zero", abs(value_of_plane_equation)


def get_radius(point, site_pos, lattice):
    """
    Gets the distance from an atom to the minimum point along partitioning line
    between it and another atom.
    """
    real_site_pos = get_real_from_vox(site_pos, lattice)
    radius = sum([(b - a) ** 2 for a, b in zip(real_site_pos, point)]) ** (0.5)
    return radius

def check_closest_neighbor_for_same_type(closest_neighbors, structure):
    """
    This function checks indirectly for covalency by checking if an atom's
    closest neighbor is an atom of the same type. This suggests that the
    atoms are covalently bonded. This is to account for the fact that in the
    check_structure_for_covalency method, we skip any atom pairs that are the
    same since they are likely to return as covalent regardless of how far apart
    they are.
    """
    # we initially assume that the closest atom is not one of the same type.
    same_atom_close = False
    for site_index, neighs in closest_neighbors.items():
        # get site atom string
        specie = structure[site_index].species_string
        # if the species is He, it is a dummy atom in an electride site and we
        # want to skip it
        if specie == "He": 
            continue
        
        # to check if the closest atom is the same type of atom, we need ot find
        # which atom is closest and which of the same atom is closest. First we
        # make lists for all nearby atom distances and same atom distances.
        site_distances = []
        same_atom_distances = []
        
        # Now we find the sites coordinates and loop over each of its neighbors
        # to find their coords. For each we find the distance away and add the
        # distance to our distances list. If they are the same atom type we also
        # add them to the same_atom_distances list.
        site_coords = structure[site_index].coords
        for neigh in neighs:
            neigh_coords = neigh["site"].coords
            site_distances.append(math.dist(site_coords, neigh_coords))
            #check that the neighbors are the same species
            if neigh["site"].specie == specie:
                same_atom_distances.append(math.dist(site_coords, neigh_coords))
        closest_atom_dist = min(site_distances)
        # find the closest atom of the same type. Sometimes this doesn't exist
        # in the nearest neighbors set so we set this to a large distance.
        try: closest_same_atom_dist = min(same_atom_distances)
        except: closest_same_atom_dist = 10
        # if the closest atom is an atom of the same time, we 
        if closest_same_atom_dist <= closest_atom_dist:
            same_atom_close = True
            break
    # if the same atom is found as the closest atom, we want to raise an error
    if same_atom_close:
        raise Exception(
            """
            An atom's closest neighbor was found to be an atom of the same type.
            This very likely indicates that these atoms are bonded covalently.
            Unfortunately, the current version of BadELF does not have a way to 
            partition peaks in the ELF from covalency, thoug this will hopefully 
            be implemented in a future version of the algorithm.
            """
            )

            
def check_structure_for_covalency(closest_neighbors, grid, lattice, structure):
    """
    This function is designed to check for covalency along the bonds from each 
    atom to its nearest neighbors. The NN are defined by Pymatgen's CrystalNN 
    function and covalency is described as a maximum in the ELF that is closer
    to the center of the bond than any minimum.
    """
    for site_index, neighs in closest_neighbors.items():
        # get voxel position from fractional site
        site_pos = get_voxel_from_index(site_index, lattice)
        # iterate over each neighbor bond
        for neigh_index, neigh in enumerate(neighs):
            # Check that we are not looking between two of the same atom. This
            # is likely to have some amount of ELF between the two atoms even
            # if they are not likely to actually be bonded with one another. I
            # don't think this should cause any issues with the algorithm, but
            # !!! it's worth testing
            site_species = structure[site_index].species_string
            neigh_species = structure[neigh["site_index"]].species_string
            
            if site_species == neigh_species:
                continue
            
            # neigh_site_index = neigh["site_index"]
            # if site_index == neigh_site_index:
            #     continue

            
            neigh_pos = get_voxel_from_neigh_CrystalNN(neigh, lattice)
            values = get_partitioning_line_rough(site_pos, neigh_pos, grid)[1]
            
            #smooth line:
            smoothed_values = savgol_filter(values, 20, 3)
            
            # Now we check for any strong covalency in the bond as in the current version
            # of BadELF, this will break the partitioning scheme
            if check_bond_for_covalency(smoothed_values):
                # import matplotlib.pyplot as plt
                # plt.plot(smoothed_values)
                raise Exception(
                    """
                    A maximum in the ELF line between atoms was found closer to the
                    center of the bond than any local minimum.
                    This typically indicates that there is some covalent behavior in
                    your system. Unfortunately, the current version of BadELF does not
                    have a way to partition peaks in the ELF from covalency, though
                    this will hopefully be implemented in a future version of the
                    algorithm.
                    
                    An alternative issue is that you are using a pseudopotential that
                    does not include more than the minimum valence electrons. This will
                    result in ELF values close to 0 around the core of the atom. Make
                    sure you are using suitable pseudopotentials for all of your atoms.
                    We are aware of at least two atoms, Al and B, that do not have a
                    suitable pseudopotential with core electrons in VASP 5.X.X.
                    """
                    )

def get_site_neighbor_results_rough(
    site_index, neigh, lattice: dict, site_pos: dict, grid, rough_partitioning=False
):
    """
    Function for getting the line, plane, and other information between a site
    and neighbor.
    """
    neigh_pos = get_voxel_from_neigh(neigh, lattice)

    # we need a straight line between these two points.  get list of all ELF values
    elf_positions, elf_values_rough = get_partitioning_line_rough(
        site_pos, neigh_pos, grid
    )

    # find the minimum position and value along the elf_line
    # the third element is the fractional position, measured from site_pos
    elf_min_index, elf_min_value, elf_min_frac = get_line_frac_min_rough(
        elf_values_rough, rough_partitioning=rough_partitioning
    )

    # convert the minimum in the ELF back into a position in the voxel grid
    elf_min_vox = get_position_from_min(elf_min_frac, site_pos, neigh_pos)

    # a point and normal vector describe a plane
    # a(x-x1) + b(y-y1) + c(z-z1) = 0
    # a,b,c is the normal vecotr, x1,y1,z1 is the point

    # convert this voxel grid_pos back into the real_space
    plane_point = get_real_from_vox(elf_min_vox, lattice)

    # get the plane perpendicular to the position.
    plane_vector = get_unit_vector(site_pos, neigh_pos, lattice)

    # it is also helpful to know the distance of the minimum from the site
    distance = get_radius(plane_point, site_pos, lattice)
    return [
        site_index,
        site_pos,
        neigh,
        neigh_pos,
        plane_point,
        plane_vector,
        distance,
        elf_positions,
        elf_values_rough,
        elf_min_index,
        elf_min_value,
        elf_min_frac,
        elf_min_vox,
    ]


def get_site_neighbor_results_fine(site_df, grid, lattice):
    # iterate through each neighbor in the dataframe and update the partitioning
    # plane info
    for row in site_df.iterrows():
        # get necessary information from the rough dataframe
        elf_positions = row[1]["elf_positions"]
        elf_min_index = row[1]["elf_min_index"]
        site_pos = row[1]["site_pos"]
        neigh_pos = row[1]["neigh_pos"]
        
        # get the minimum position along the elf line
        (   elf_min_index_new,
            elf_min_value_new,
            elf_min_frac_new,
        ) = get_line_frac_min_fine(elf_positions, elf_min_index, grid)

        # convert minimum in ELF line into voxel position
        elf_min_vox = get_position_from_min(elf_min_frac_new, site_pos, neigh_pos)
        # convert voxel position into real_space
        plane_point = get_real_from_vox(elf_min_vox, lattice)
        # get the new distance between the site and the plane point
        distance = get_radius(plane_point, site_pos, lattice)
        # update the dataframe
        row[1]["elf_min_index"] = elf_min_index_new
        row[1]["elf_min_value"] = elf_min_value_new
        row[1]["elf_min_frac"] = elf_min_frac_new
        row[1]["plane_point"] = plane_point
        row[1]["distance"] = distance
        row[1]["elf_min_vox"] = elf_min_vox
    return site_df


def get_partitioning_rough(neighbors50, lattice, grid, rough_partitioning=False):
    # Now we want to find the minimum in the ELF between the atom and each of its
    # neighbors and the vector between them. This will define a plane seperating
    # the atom from its neighbor.

    # iterate through each site in the structure
    rough_partition_results = []
    columns = [
        "site_index",
        "site_pos",
        "neigh",
        "neigh_pos",
        "plane_point",
        "plane_vector",
        "distance",
        "elf_positions",
        "elf_values_rough",
        "elf_min_index",
        "elf_min_value",
        "elf_min_frac",
        "elf_min_vox",
    ]
    for site_index, neighs in enumerate(neighbors50):
        # create df for each site
        site_df = pd.DataFrame(columns=columns)
        # get voxel position from fractional site
        site_pos = get_voxel_from_index(site_index, lattice)
        # site_pos_real = get_real_from_vox(site_pos, lattice)
        # iterate through each neighbor to the site
        for i, neigh in enumerate(neighs):
            site_df.loc[len(site_df)] = get_site_neighbor_results_rough(
                site_index, neigh, lattice, site_pos, grid, rough_partitioning
            )


        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # For now I am treating partitioning in a static way by just using 50 
        # partitioning planes no matter the atom or system. I believe plane
        # selection is the source for many errors in voxel assignment.
        # I will update this in the future to more rigorously select the planes.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # # # create a list to store the final set of neighbors
        important_neighs = pd.DataFrame(columns=columns)
        for [index, row] in site_df.iterrows():
            important_neighs.loc[len(important_neighs)] = row
        rough_partition_results.append(important_neighs)

    if rough_partitioning:
        results = {}
        for site_index, site_df in enumerate(rough_partition_results):
            neigh_dict = {}
            for neigh_row in site_df.iterrows():
                # convert dataframe row into a dictionary
                site_neigh_dict = {}
                site_neigh_dict["vox_site"] = neigh_row[1]["site_pos"]
                site_neigh_dict["vox_neigh"] = neigh_row[1]["neigh_pos"]
                site_neigh_dict["value_elf"] = neigh_row[1]["elf_min_value"]
                site_neigh_dict["pos_elf_frac"] = neigh_row[1]["elf_min_frac"]
                site_neigh_dict["vox_min_point"] = neigh_row[1]["elf_min_vox"]
                site_neigh_dict["real_min_point"] = neigh_row[1]["plane_point"]
                site_neigh_dict["normal_vector"] = neigh_row[1]["plane_vector"]
                site_neigh_dict["sign"] = "negative"
                site_neigh_dict["radius"] = neigh_row[1]["distance"]
                site_neigh_dict["neigh"] = neigh_row[1]["neigh"]
                # site_neigh_dict["elf_line"] = smoothed_line
                site_neigh_dict["elf_line_raw"] = neigh_row[1]["elf_values_rough"]
                # adding some results for testing
                site_neigh_dict["neigh_index"] = neigh_row[1]["neigh"].index
                # site_neigh_dict["neigh_distance"] = math.dist(real_site_point, real_neigh_point)

                # add row dictionary to neighbor dictionary
                neigh_dict[neigh_row[0]] = site_neigh_dict

            # add the neighbor dictionary to the results dictionary
            results[site_index] = neigh_dict
        return results
    else:
        return rough_partition_results


def get_partitioning_fine(rough_partition_results, grid, lattice):
    results = {}
    for site_index, site_df in enumerate(rough_partition_results):
        fine_site_df = get_site_neighbor_results_fine(site_df, grid, lattice)
        neigh_dict = {}
        for neigh_row in fine_site_df.iterrows():
            # convert dataframe row into a dictionary
            site_neigh_dict = {}
            site_neigh_dict["vox_site"] = neigh_row[1]["site_pos"]
            site_neigh_dict["vox_neigh"] = neigh_row[1]["neigh_pos"]
            site_neigh_dict["value_elf"] = neigh_row[1]["elf_min_value"]
            site_neigh_dict["pos_elf_frac"] = neigh_row[1]["elf_min_frac"]
            site_neigh_dict["vox_min_point"] = neigh_row[1]["elf_min_vox"]
            site_neigh_dict["real_min_point"] = neigh_row[1]["plane_point"]
            site_neigh_dict["normal_vector"] = neigh_row[1]["plane_vector"]
            site_neigh_dict["sign"] = "negative"
            site_neigh_dict["radius"] = neigh_row[1]["distance"]
            site_neigh_dict["neigh"] = neigh_row[1]["neigh"]
            # site_neigh_dict["elf_line"] = smoothed_line
            site_neigh_dict["elf_line_raw"] = neigh_row[1]["elf_values_rough"]
            # adding some results for testing
            site_neigh_dict["neigh_index"] = neigh_row[1]["neigh"].index
            # site_neigh_dict["neigh_distance"] = math.dist(real_site_point, real_neigh_point)

            # add row dictionary to neighbor dictionary
            neigh_dict[neigh_row[0]] = site_neigh_dict

        # add the neighbor dictionary to the results dictionary
        results[site_index] = neigh_dict
    return results


###############################################################################
# This section defines functions that are used for assigning voxels that aren't
# split by a plane to the correct atomic site.
# This includes functions that determine which voxels might be split by a plane,
# find which site a voxel should belong to, and parallelize this across a Dask
# partitioned Dataframe.
###############################################################################


def get_max_voxel_dist(lattice):
    """
    Finds the maximum distance a voxel can be from a dividing plane that still
    allows for the possibility that the voxel is intercepted by the plane.

    First finds the center and vertices of a voxel with its corner at the origin.
    The center is the same as the centroid of the vectors making up the
    unit cell scaled down to the size of one voxel
    """
    # We need to find the coordinates that make up a single voxel. This
    # is just the cartesian coordinates of the unit cell divided by
    # its grid size
    end = [0, 0, 0]
    vox_a = [x / lattice["grid_size"][0] for x in lattice["a"]]
    vox_b = [x / lattice["grid_size"][1] for x in lattice["b"]]
    vox_c = [x / lattice["grid_size"][2] for x in lattice["c"]]
    # We want the three other vertices on the other side of the voxel. These
    # can be found by adding the vectors in a cycle (e.g. a+b, b+c, c+a)
    vox_a1 = [x + x1 for x, x1 in zip(vox_a, vox_b)]
    vox_b1 = [x + x1 for x, x1 in zip(vox_b, vox_c)]
    vox_c1 = [x + x1 for x, x1 in zip(vox_c, vox_a)]
    # The final vertex can be found by adding the last unsummed vector to any
    # of these
    end1 = [x + x1 for x, x1 in zip(vox_a1, vox_c)]
    # The center of the voxel sits exactly between the two ends
    center = [(x + x1) / 2 for x, x1 in zip(end, end1)]
    # Shift each point here so that the origin is the center of the
    # voxel.
    voxel_vertices = []
    for vector in [center, end, vox_a, vox_b, vox_c, vox_a1, vox_b1, vox_c1, end]:
        new_vector = [(x - x1) for x, x1 in zip(vector, center)]
        voxel_vertices.append(new_vector)

    # Now we need to find the maximum distance from the center of the voxel
    # to one of its edges. This should be at one of the vertices.
    # We can't say for sure which one is the largest distance so we find all
    # of their distances and return the maximum
    max_distance = max([np.linalg.norm(vector) for vector in voxel_vertices])
    return max_distance


def get_matching_site(pos, results, lattice, max_distance):
    """
    Determines which atomic site a point belongs to.
    """
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # I've had a bug in the past where more than one site is found for a single
    # voxel. As such, I'm going to temporarily make this function search all
    # sites in case it finds more than one. This bug seemed to be due to incorrect
    # plane selection.
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    sites = []
    # Iterate over each site in the lattice
    for site, neighs in results.items():
        matched = True
        # Iterate through each neighbor
        for neigh, values in neighs.items():
            # get the minimum point and normal vector which define the plane
            # seperating the sites.
            try:
                point = values["real_min_point"]
            except:
                breakpoint()
            normal_vector = values["normal_vector"]
            # If a voxel is on the same side of the plane as the site, then they
            # should have the same sign when their coordinates are plugged into
            # the plane equation (negative).
            # expected_sign = values["sign"]

            # use plane equation to find sign
            sign, distance = get_plane_sign(point, normal_vector, pos, lattice)

            # if the sign matches, move to next neighbor.
            # if the sign ever doesn't match, then the site is wrong and we move
            # on to the next one after setting matched to false. We also check
            # to see if the voxel is possibly sliced by the plane. If it is we
            # want to seperate that charge later so we leave it here.
            if sign != "negative" or distance <= max_distance:
                matched = False
                break
        if matched == True:
            sites.append(site)
            # return site
    if len(sites) == 1:
        return sites[0]
    elif len(sites) == 0:
        return
    else:
        # Multiple sites found for one location
        return -1

def get_electride_sites(
    lattice: dict,
):
    """
    Function for getting the number of sites that are electrides
    """
    # Create list for electride site index
    electride_sites = []
    # Create integer values for the number of sites before the electride and
    # the number of electrides
    sites_before_electride = int(0)
    sites_of_electride = int()
    # When creating dummy atoms in electrides we usually use He because there
    # are so few materials that contain it.
    if "He" in lattice["elements"]:
        # iterates over element labels and finds the index for electride sites
        for i, element in enumerate(lattice["elements"]):
            if element == "He":
                # iterates over the number of each element. Since the electride
                # is always added at the end, we can just add up the number of
                # atoms before this point
                for j in range(i):
                    sites_before_electride += lattice["elements_num"][j]
            # We find the total number of electride sites
            sites_of_electride = lattice["elements_num"][i]
    for i in range(sites_of_electride):
        electride_sites.append(sites_before_electride + i)
    return electride_sites


def get_voxels_site(
    x,
    y,
    z,
    site,
    results,
    permutations,
    lattice,
    electride_sites,
    max_distance,
):
    """
    Finds the site a voxel belongs to. Mostly does the same as the
    get_matching_site function, but also checks other possible symmetric locations
    of each site.
    """
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # I've had a bug in the past where one voxel returns multiple sites after
    # being translated. I'm going to make this function temporarily go through
    # all sites in case the bug still exists. It will return -1 if the multiple
    # sites are found at the same transformation and it will return -2 if multiple
    # are found across different transformations. This bug seemed to be due to
    # insufficient partitioning plane selection
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    sites = []
    if site not in electride_sites:
        for t, u, v in permutations:
            new_pos = [x + t, y + u, z + v]
            site: int = get_matching_site(new_pos, results, lattice, max_distance)
            # site returns none if no match, otherwise gives a number
            # The site can't return as an electride site as we don't include
            # electride sites in the partitioning results
            if site == -1:
                # If the site returns -1, this means multiple sites were found
                # at one transformation which should never happen. I want this
                # function to return -1 so I can count how often this happens
                # if at all.
                sites = []
                sites.append(-1)
                break
            elif site is not None:
                sites.append(site)
                # break
    if len(sites) > 1:
        # if the length of sites is greater than 1 that means it found more than
        # one site at different transformations. I want to return -2 so I can
        # keep track of how often this bug occurs.
        return -2
    elif len(sites) == 1:
        # there is only one site found so we just return it.
        return sites[0]
    else:
        # there wasn't any site found so we don't return our site variable which
        # is None
        return site
    return site


def get_voxels_site_dask(
    df,
    results: dict,
    permutations: list,
    lattice: dict,
    electride_sites: list,
    max_distance: float,
):
    """
    This defines a secondary function that runs get_voxel_site across a pandas
    DataFrame. this allows us to run the function across a Dask partitioned
    DataFrame.
    """
    return df.apply(
        lambda x: get_voxels_site(
            x["x"],
            x["y"],
            x["z"],
            x["site"],
            results,
            permutations,
            lattice,
            electride_sites,
            max_distance,
        ),
        axis=1,
    )


###############################################################################
# This section defines functions that are used for assigning voxels that ARE
# split by a plane
# This includes functions that find the vertices of a voxel, which site they
# belong to, where a plane intersects a given voxel, and what volume ratio of
# each voxel belongs to a given site.
###############################################################################

def get_matching_site_with_plane(vert_coord, results, lattice):
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # I've had a bug in the past where more than one site is found for a single
    # voxel location. As such, I'm going to temporarily make this function search all
    # sites in case it finds more than one. This bug seemed to be caused by
    # insufficient partitioning plane selection.
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    sites = []
    # Iterate over each site in the lattice
    for site, neighs in results.items():
        matched = True
        # Iterate through each neighbor
        for neigh, values in neighs.items():
            # get the minimum point and normal vector which define the plane
            # seperating the sites.
            try:
                point = values["real_min_point"]
            except:
                breakpoint()
            normal_vector = values["normal_vector"]
            # If a voxel is on the same side of the plane as the site, then they
            # should have the same sign when their coordinates are plugged into
            # the plane equation (negative).

            # use plane equation to find sign
            sign, distance = get_plane_sign(point, normal_vector, vert_coord, lattice)

            # if the sign matches, move to next neighbor.
            # if the sign ever doesn't match, then the site is wrong and we move
            # on to the next one after setting matched to false. We also check
            # to see if the voxel is possibly sliced by the plane. If it is we
            # want to seperate that charge later so we leave it here.
            if sign != "negative":
                matched = False
                break
        if matched == True:
            sites.append(site)
            # return site
    if len(sites) == 1:
        return sites[0]
    elif len(sites) == 0:
        return
    else:
        # Multiple sites found for one vertex location
        return -1

def get_vertex_site(
    x,
    y,
    z,
    results,
    permutations,
    lattice,
):
    """
    Finds the site a voxel belongs to. Mostly does the same as the
    get_matching_site function, but also checks other possible symmetric locations
    of each site.
    """
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # I've noticed a bug where one voxel returns multiple sites after
    # being translated. I'm going to make this function temporarily go through
    # all sites in case the bug still exists. It will return -1 if the multiple
    # sites are found at the same transformation and it will return -2 if multiple
    # are found across different transformations. This typically effects only
    # a small number of sites if the system is ionic. This bug seemed to be
    # caused by insufficient partitioning plane selection
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    sites = []
    translations = []
    for t, u, v in permutations:
        new_vert_coord = [x + t, y + u, z + v]
        site: int = get_matching_site_with_plane(new_vert_coord, results, lattice)
        # site returns none if no match, otherwise gives a number
        # The site can't return as an electride site as we don't include
        # electride sites in the partitioning results
        if site == -1:
            # If the site returns -1, this means multiple sites were found
            # at one transformation which should never happen. I want this
            # function to return -1 so I can count how often this happens
            # if at all.
            sites = []
            sites.append(-1)
            break
        elif site is not None:
            sites.append(site)
            translations.append([t, u, v])
            # break
    if len(sites) > 1:
        # if the length of sites is greater than 1 that means it found more than
        # one site at different transformations. I want to return -2 so I can
        # keep track of how often this bug occurs.
        return -2, None
    elif len(sites) == 1:
        # there is only one site found so we just return it.
        return sites[0], translations[0]
    else:
        # there wasn't any site found so we don't return our site variable which
        # is None
        return site
    return site


def get_vertices_coords(vox_coord, results, lattice, permutations):
    """
    Takes in the coordinates of a voxel and returns the site that matches
    each of its vertices.
    """
    # create a dictionary to store the vertices coordinates and the site results
    vertices_coords = {}
    keys = ["A0", "A1", "A2", "A3", "B0", "B1", "B2", "B3"]
    # we need to transform the voxel coordinates to 8 different half coordinates
    # that represent its corners
    A0 = [-1 / 2, -1 / 2, -1 / 2]
    A1 = [-1 / 2, 1 / 2, -1 / 2]
    A2 = [1 / 2, 1 / 2, -1 / 2]
    A3 = [1 / 2, -1 / 2, -1 / 2]
    B0 = [-1 / 2, -1 / 2, 1 / 2]
    B1 = [-1 / 2, 1 / 2, 1 / 2]
    B2 = [1 / 2, 1 / 2, 1 / 2]
    B3 = [1 / 2, -1 / 2, 1 / 2]
    transforms = [A0, A1, A2, A3, B0, B1, B2, B3]
    for key, transform in zip(keys, transforms):
        vertices_coords[key] = [x + x1 for x, x1 in zip(vox_coord, transform)]

    # create a dataframe to store results in
    vertices_sites = pd.DataFrame(columns=["id", "transform", "site"])

    # now that we have the coordinates for each vertex, get the site and the
    # transform required to get the site
    for key, coord in vertices_coords.items():
        x, y, z = coord
        try:
            site, transform = get_vertex_site(x, y, z, results, permutations, lattice)
            vertex_row = [key, transform, site]
            vertices_sites.loc[len(vertices_sites.index)] = vertex_row
        # If we can't find a site, return an empty row for this key
        except:
            vertex_row = [key, None, None]
            vertices_sites.loc[len(vertices_sites.index)] = vertex_row
    # return both the vertices coords and the information about their sites
    return vertices_coords, vertices_sites


def get_vector_plane_intersection(
    point0, point1, plane_point, plane_vector, allow_point_intercept=False
):
    """
    Takes in two points and the point/vector defining a plane and returns
    the point where the line segment and plane intersect (if it exists)
    """
    # convert points to NumPy arrays
    point0 = np.array(point0)
    point1 = np.array(point1)
    plane_point = np.array(plane_point)
    plane_vector = np.array(plane_vector)

    # get direction of line segment.
    direction = point1 - point0
    # get dot product of direction vector and dot_product
    dot_product = np.dot(direction, plane_vector)
    # check if line is parallel to plane
    if np.abs(dot_product) < 1e-06:
        return None

    # get distance from the line segment point to the plane
    distance = np.dot(plane_point - point0, plane_vector) / dot_product

    # calculate intersection point
    intersection_point = point0 + direction * distance
    # round the intersection points

    # check if intersection point is between the start and end points of our
    # line segment. To do this, we would normally first check if the point
    # is on the line, but it must be alredy because we defined it as such. Next
    # we check the dot products
    # Get the vector for the intersecting point and point1 assuming point0 is
    # the origin
    AB = point1 - point0
    AC = intersection_point - point0
    # Get the dot products of the intersecting point and point1
    KAC = np.dot(AB, AC)
    KAB = np.dot(AB, AB)
    # There are five possible scenarios.
    if KAC < -1e-8 or KAC > KAB + 1e-8:
        # the point is outside the line
        return None
    elif KAC == 0 or KAC == KAB:
        # The point is at point0 or point1
        if allow_point_intercept:
            return intersection_point
        else:
            return None
    else:
        # The point is between point0 and point1
        return intersection_point


def get_intersections_df(
    sites, results, edges, transformed_coords_real, intersections_df
):
    """
    Function for finding which planes intersect a voxel. Returns dataframe
    with all planes and intersections
    """
    # We create a list of sites that we want to allow in the plane intersections
    # search. Each plane is stored twice: once for each atom in the pair. Because
    # of this we remove each site after we've looked at its planes to remove
    # redundancy
    sites_to_search = sites["site"].to_list()
    for site in sites["site"]:
        sites_to_search.remove(site)
        # iterate over each plane
        for neighbor, values in results[site].items():
            neighbor_index = values["neigh_index"]
            # if neighbor is in the list of sites, look at the plane
            if neighbor_index in sites_to_search:
                plane_point = values["real_min_point"]
                plane_vector = values["normal_vector"]
                # iterate over each edge and find the points that intersect
                intersections = []
                for edge in edges:
                    point0 = transformed_coords_real[edge[0]]
                    point1 = transformed_coords_real[edge[1]]
                    intersection = get_vector_plane_intersection(
                        point0, point1, plane_point, plane_vector
                    )
                    if intersection is not None:
                        # we transform all intersections to be relative to A0 being
                        # the origin. This is so planes from various transformations
                        # can be treated at the same time
                        # MUST ROUND!
                        intersection = [
                            round((x - x1), 12)
                            for x, x1 in zip(
                                intersection, transformed_coords_real["A0"]
                            )
                        ]
                        intersections.append(intersection)
                if len(intersections) > 0:
                    # if we have any intersections we add the site index, its
                    # neighbors index, and the list of intersections to the df
                    plane_row = [site, values["neigh_index"], intersections]
                    intersections_df.loc[len(intersections_df)] = plane_row
    return intersections_df


def get_site_volume_ratio(x, y, z, results, lattice, permutations, voxel_volume):
    """
    Takes in the coordinates for the vertices of a voxel and returns the
    volumes that should be applied to these sites as a ratio in a dictionary.
    """
    # get the coordinates and site/plane information about each vertex.
    vox_coord = [x, y, z]

    vertices_coords, vertices_sites = get_vertices_coords(
        vox_coord, results, lattice, permutations
    )
    # Define edges for the voxel
    edges = [
        ["A0", "A1"],
        ["A1", "A2"],
        ["A2", "A3"],
        ["A3", "A0"],
        ["A0", "B0"],
        ["A1", "B1"],
        ["A2", "B2"],
        ["A3", "B3"],
        ["B0", "B1"],
        ["B1", "B2"],
        ["B2", "B3"],
        ["B3", "B0"],
    ]

    # create dictionary for recording what fraction of a voxels volume should
    # be associated with a given site.
    site_vol_frac = {}
    for site in results.keys():
        site_vol_frac[site] = float(0)

    # shorten the lists to unique sites/planes
    sites = vertices_sites.drop_duplicates(subset="site", ignore_index=True)
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # I've made it so that if multiple sites are found for one vertex position,
    # it returns as -1. If multiple sites are found for one vertex but at multiple
    # transformed positions it returns -2.
    # My best guess for what is happening is that these sites are very close to
    # being exactly on a plane and are therefore returning as being part of
    # more than one site.
    # In a test with Na2S, returning these vertices as None and allowing the
    # program to continue gave more even results.
    if -1 in sites["site"].to_list() or -2 in sites["site"].to_list():
        # If vertices are found to have multiple sites I've made it so that it
        # records his information as a new site in the site_vol_frac dictionary.
        # This should be searchable in post so that I can keep count of these
        # without stopping the algorithm
        if -1 in sites["site"].to_list():
            site_vol_frac[-1] = float(0)
        elif -2 in sites["site"].to_list():
            site_vol_frac[-2] = float(0)
        sites = sites.replace(-1, None)
        sites = sites.replace(-2, None)
        # sites.replace()
        # breakpoint()
    # find the most common site for cases where only one site exists
    try:
        most_common_site = sites["site"].value_counts().idxmax()
    except:
        most_common_site = None
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    sites = sites.dropna(subset="site").reset_index()

    # define the dataframe that we will store our plane information in
    intersections_df = pd.DataFrame(columns=["site", "neighbor", "intersections"])

    # Sometimes the voxel will be intersected only at certain transformations.
    # Often this is the permutation where the original voxel was able to be
    # assigned to an atomic site. We check this possibility first here. Sometimes,
    # the vertices themselves are shifted to other permutations. We check these
    # next.

    # Get the transform for the original site:
    try:
        voxel_site, transform = get_vertex_site(x, y, z, results, permutations, lattice)
    except:
        voxel_site, transform = None, None


    # If no intersections are found, check the other possible transforms
    if len(intersections_df) == 0:
        # Get the list of possible transforms for the dataframe of sites and
        # transforms we found earlier
        transforms = vertices_sites.drop_duplicates(subset="transform").dropna()
        transforms = transforms["transform"].to_list()

        # Now iterate over the remaining transforms to find locations where the
        # edge is intersected.
        for transform in transforms:
            transformed_coords_real = {}
            for key, coord in vertices_coords.items():
                # get the transformed coordinate, convert it to a real coordinate,
                # and add to our new dictionary of vertices
                new_coord = [x + t for x, t in zip(coord, transform)]
                real_coord = get_real_from_vox(new_coord, lattice)
                transformed_coords_real[key] = real_coord
            # get any intersections between planes and voxel edges and add to
            # our intersection dataframe
            intersections_df = get_intersections_df(
                sites, results, edges, transformed_coords_real, intersections_df
            )
    # It's possible for the plane to intersect a vertex exactly causing there
    # to be multiple instances of the same intersection. Remove any duplicates
    # this may cause.
    intersections_df = intersections_df.drop_duplicates(subset="intersections")

    # We shift all intersections to the origin in case there are multiple
    # planes intersecting at different transforms. We also need to shift all
    # of the vertices so that they are relative to the origin.
    vertices_coords_real_origin = {}
    # convert coordinate to real for use later
    for key, coord in vertices_coords.items():
        # transform so that A0 is at origin
        transformed_coord = [x - x1 + 1 for x, x1 in zip(coord, vertices_coords["A0"])]
        # add the real coord to our dictionary of vertices
        vertices_coords_real_origin[key] = get_real_from_vox(transformed_coord, lattice)

    # Now that we have a list of plane intersections, we can find the what portion
    # of the voxels should be applied to each site.
    # If there is only one site in the list, return the site fraction dictionary
    # with 1 for this site.
    if len(sites) == 1:
        if voxel_site is not None:
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # Sometimes the voxel center is returned as belonging to more than
            # 1 site. I beleive this is because without the condition that the
            # voxel needs to be some distance away from the plane (Which exists
            # when we assign planes earlier in the code.) it is actually possible
            # for a plane to exactly go through the site resulting in it
            # being allowed to belong to two sites. In this situation I don't want
            # to give the voxel to a -2 site, I want it to go to the most common
            # site.
            if voxel_site == -1 or voxel_site == -2:
                try:
                    site_vol_frac[most_common_site] = 1.0
                except:
                    site_vol_frac = None
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            elif len(intersections_df) == 0 or len(intersections_df) == 1:
                site_vol_frac[voxel_site] = 1.0
            else:
                site_vol_frac = None
        else:
            site_vol_frac = None
    # If there are two sites, at least one plane is intersecting the voxel
    elif len(sites) == 2:
        # if there are not intersections found, then something is not working
        if len(intersections_df) == 0:
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # I'm having this problem return as -3 so that I can keep track of it
            site_vol_frac[-3] = float(0)
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Check that there is only one plane that is close to all of the vertices.
        # If so, our voxel is being split by a single plane.
        elif len(intersections_df) == 1:
            # get a list of the intersecting points
            intersect_points = list(intersections_df["intersections"])[0]

            # If there are no intersect points, there is an error somewhere
            # above and we want to stop the process.
            if len(intersect_points) == 0:
                breakpoint()
            else:
                # define a list to populate with the points that make up one section
                # of the voxel
                site_points = []
                # define the two sites that the voxel will be split into
                site1 = sites["site"].iloc[0]
                site2 = sites["site"].iloc[1]
                # iterate over the vertices and if they belong to the first site
                # append them to our site points list
                for row in vertices_sites.iterrows():
                    if row[1]["site"] == site1 or row[1]["site"] is None:
                        site_points.append(
                            np.array(vertices_coords_real_origin[row[1]["id"]])
                        )
                    # otherwise we don't do anthing
                # combine the list of vertex coordinates with the list of intersections

                hull_points = []
                # Add all vertex points to the list
                for site_point in site_points:
                    hull_points.append(np.array(site_point))
                # If intersect points are found very close to a vertex point, we
                # don't want to accidentally double count. Here we check each
                # point before adding it to the list of hull points.
                for intersect_point in intersect_points:
                    intersect_array = np.array(intersect_point)
                    repeat = False
                    for site_point in site_points:
                        site_array = np.array(site_point)
                        if np.allclose(intersect_array, site_array, rtol=0, atol=1e-6):
                            repeat = True
                            break
                        else:
                            pass
                    if repeat == False:
                        hull_points.append(intersect_array)

                # define a 3D convex hull for the first segment. Get its volume, then
                # use the ratio of its volume to the total voxel volume to find the
                # ratio of charge that should be applied to each voxel
                try:
                    hull = ConvexHull(hull_points)
                    seg1_vol = hull.volume
                    seg1_ratio = round((seg1_vol / voxel_volume), 16)
                    site_vol_frac[site1] = seg1_ratio
                    site_vol_frac[site2] = round((1 - seg1_ratio), 16)
                except:
                    print(f"Error with hull: {[x,y,z]}")
                    site_vol_frac = None

        elif len(intersections_df) > 1:
            # if there is more than one plane, the voxel is being split in
            # multiple ways. For now we just return no site_vol_frac because
            # we won't be handling this rigorously
            site_vol_frac = None
    # if there are more than two sites or more than one planes, the voxel is
    # being split by more than one plane. For now I'm just passing these on
    else:
        site_vol_frac = None
    return site_vol_frac


def get_voxels_site_volume_ratio_dask(
    df,
    results: dict,
    lattice: dict,
    permutations: list,
    voxel_volume: float,
):
    """
    Applies the get_voxels_site_volume_ration function across a Pandas dataframe.
    """
    return df.apply(
        lambda x: get_site_volume_ratio(
            x["x"],
            x["y"],
            x["z"],
            results=results,
            lattice=lattice,
            permutations=permutations,
            voxel_volume=voxel_volume,
        ),
        axis=1,
    )


def get_voxels_site_multi_plane(
    x,
    y,
    z,
    pdf,
    near_plane_pdf,
    lattice: dict,
    electride_sites: list,
    results: dict,
):
    """
    This function finds what sites a voxel divided by more than one plane should
    be applied to. It looks at nearby voxels and finds what sites they are applied
    to and finds the ratio between these sites.
    """
    # create dictionary for counting number of sites and for the fraction
    # of sites
    site_count = {}
    site_frac = {}
    for site in results.keys():
        site_count[site] = int(0)

    # look at all neighbors and tally which site they belong to.
    for t, u, v in itertools.product([-1, 0, 1], [-1, 0, 1], [-1, 0, 1]):
        new_idx = [x - 1 + t, y - 1 + u, z - 1 + v]

        # wrap around for voxels on edge of cell
        new_idx = [a % b for a, b in zip(new_idx, lattice["grid_size"])]

        # get site from the sites that have already been found using the sites
        # index. This is much faster than searching by values. To get the index
        # we can utilize the fact that an increase in z will increase the index
        # by 1, an increase in y will increase the index by (range of z),
        # and an increase in x will increase the index by (range of z)*(range of y)
        zrange = lattice["grid_size"][2]
        yrange = lattice["grid_size"][1]
        index = int((new_idx[0]) * zrange * yrange + (new_idx[1]) * zrange + new_idx[2])
        site = pdf["site"].iloc[index]
        # If site exists and isn't an electride site, add to the count. This
        # will prevent the nearby sites from ever being mostly electride.
        if site is not None and site not in electride_sites:
            site_count[site] += 1
        # If site doesn't exist, check the near plane pdf to see if the
        # site was split into multiple
        elif site is None and site not in electride_sites:
            # near_plane_pdf_index = near_plane_pdf.reset_index()
            try:
                site_dict = near_plane_pdf.loc[index]["site"]
                if site_dict is not None:
                    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    # I've made it so that there can be a site labeled -3, -2,
                    # or -1. I don't want these to be counted here so I'm
                    # skipping them
                    for site_index, frac in site_dict.items():
                        if site_index in [-3, -2, -1]:
                            continue
                        else:
                            site_count[site_index] += frac
                    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            except:
                pass
    # ensure that some sites were found
    if sum(site_count.values()) != 0:
        # get the fraction of each site. This will allow us to split the
        # charge of the voxel more evenly
        for site_index in site_count:
            site_frac[site_index] = site_count[site_index] / sum(site_count.values())
    return site_frac


def get_voxels_site_nearest(
    x,
    y,
    z,
    permutations: list,
    lattice: dict,
):
    """
    This function finds the closest atom to a voxel.
    """
    # create lists to store site indices and distances
    sites = []
    distances = []

    # get lists of atom coordinates and site numbers
    atom_coords = lattice["coords"]
    atom_site_indices = [i for i in range(len(atom_coords))]

    for t, u, v in permutations:
        new_idx = [x + t, y + u, z + v]
        real_coord = get_real_from_vox(new_idx, lattice)
        for site, coord in zip(atom_site_indices, atom_coords):
            dist = math.dist(real_coord, coord)
            sites.append(site)
            distances.append(dist)

    # find the smallest distance
    min_dist = min(distances)
    # return the index associated with the smallest distance
    return sites[distances.index(min_dist)]
