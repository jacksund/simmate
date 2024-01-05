# -*- coding: utf-8 -*-

import math
from itertools import combinations

import numpy as np
import pandas as pd
from numpy import polyfit
from numpy.typing import ArrayLike
from pymatgen.analysis.local_env import CrystalNN
from scipy.interpolate import RegularGridInterpolator
from scipy.signal import savgol_filter
from scipy.spatial import ConvexHull

from simmate.apps.badelf.core.grid import Grid
from simmate.toolkit import Structure


class PartitioningToolkit:
    """
    A set of tools for aiding in partitioning a 3D voxel grid. These tools make
    up the basis for the partitioning utilized in BadELF and the related
    VoronELF algorithms.

    Args:
        grid (Grid): A BadELF app Grid type object.
    """

    def __init__(self, grid: Grid):
        self.grid = grid.copy()

    def get_partitioning_line(
        self,
        site_voxel_coord: ArrayLike | list,
        neigh_voxel_coord: ArrayLike | list,
        method: str = "linear",
    ):
        """
        Finds a line of voxel positions between two atom sites and then finds the value
        of the partitioning grid at each of these positions. The values are found
        using an interpolation function defined using SciPy's RegularGridInterpeter.

        Args:
            site_voxel_coord (ArrayLike): The voxel coordinates of an atomic site
            neigh_voxel_coord (ArrayLike): The voxel coordinates of a neighboring
                site
            method (str): The method of interpolation. 'cubic' is more rigorous
                than 'linear'

        Results:
            A list with 200 pairs of voxel coordinates and data values along
            a line between two positions.
        """
        grid_data = self.grid.copy().total
        steps = 200
        slope = [b - a for a, b in zip(site_voxel_coord, neigh_voxel_coord)]
        slope_increment = [float(x) / steps for x in slope]

        # get a list of points along the connecting line. First add the original
        # site
        position = site_voxel_coord
        line = [
            [
                round((float(((a - 1) % b) + 1)), 12)
                for a, b in zip(position, grid_data.shape)
            ]
        ]
        for i in range(steps):
            # move position by slope_increment
            position = [float(a + b) for a, b in zip(position, slope_increment)]

            # Wrap values back into cell
            # We must do (a-1) to shift the voxel index (1 to grid_max+1) onto a
            # normal grid, (0 to grid_max), then do the wrapping function (%), then
            # shift back onto the VASP voxel index.
            position = [
                round((float(((a - 1) % b) + 1)), 12)
                for a, b in zip(position, grid_data.shape)
            ]

            line.append(position)

        # The partitioning uses a padded grid and grid interpolation to find the
        # location of dividing planes.
        padded_grid_data = np.pad(grid_data, 1, mode="wrap")

        # interpolate grid to find values that lie between voxels. This is done
        # with a cruder interpolation here and then the area close to the minimum
        # is examened more closely with a more rigorous interpolation in
        # get_line_frac_min
        a, b, c = self.grid.get_grid_axes(1)
        fn = RegularGridInterpolator((a, b, c), padded_grid_data, method=method)
        # get a list of the ELF values along the line
        values = []

        for pos in line:
            adjusted_pos = [x for x in pos]
            value = float(fn(adjusted_pos))
            values.append(value)

        # smooth line with savgol filter
        values = savgol_filter(values, 20, 3)
        return line, values

    @staticmethod
    def _check_partitioning_line_for_symmetry(values: list, tolerance: float = 0.1):
        """
        Check if the values are roughly symmetric.

        Parameters:
        - values: List of numeric values
        - tolerance: Tolerance level for symmetry check

        Returns:
        - True if roughly symmetric, False otherwise
        """
        n = len(values)

        # Check if the list has an even number of elements
        if n % 2 != 0:
            # remove the center if odd number
            center_index = math.ceil(n / 2)
            values.pop(center_index)

        # Split the list into two halves
        half_size = n // 2
        first_half = values[:half_size]
        second_half = values[half_size:]

        # Reverse the second half
        reversed_second_half = list(reversed(second_half))

        # Check if the values are roughly equal within the given tolerance
        for val1, val2 in zip(first_half, reversed_second_half):
            if abs(val1 - val2) > tolerance:
                return False

        return True

    @staticmethod
    def find_minimum(values: list | ArrayLike):
        """
        Finds the local minima in a list of values and returns the index and value
        at each as a list of form [[min_index1, min_value1], [min_index2, min_value2], ...]

        Args:
            values (list): The list of values to find the minima of

        results:
            A list of minima represented by [index, value]
        """
        minima = [
            [i, y]
            for i, y in enumerate(values)
            if ((i == 0) or (values[i - 1] >= y))
            and ((i == len(values) - 1) or (y < values[i + 1]))
        ]
        return minima

    @staticmethod
    def find_maximum(values: list | ArrayLike):
        """
        Finds the local maxima in a list of values and returns the index and value
        at each as a list of form [[max_index1, max_value1], [max_index2, max_value2], ...]

        Args:
            values (list): The list of values to find the minima of

        results:
            A list of maxima represented by [index, value]
        """
        maxima = [
            [i, y]
            for i, y in enumerate(values)
            if ((i == 0) or (values[i - 1] <= y))
            and ((i == len(values) - 1) or (y > values[i + 1]))
        ]
        return maxima

    @staticmethod
    def get_closest_extrema_to_center(
        values: list | ArrayLike,
        extrema: list | ArrayLike,
    ):
        """
        Takes a list of values and the relative extrema (either minima or maxima)
        and finds which extrema is closest to the center of the line.

        Args:
            values (list): A list of values
            extrema (list): A list of extrema of form [index, value]

        results:
            The global extreme of form [index, value]
        """
        midpoint = len(values) / 2
        differences = []
        for pos, val in extrema:
            diff = abs(pos - midpoint)
            differences.append(diff)
        min_pos = differences.index(min(differences))
        global_extrema = extrema[min_pos]
        return global_extrema

    @classmethod
    def get_line_minimum_as_frac(
        cls,
        values: list | ArrayLike,
        site_string: str,
        neigh_string: str,
    ):
        """
        Finds the minimum point of a list of values along a line, then returns the
        fractional position of this values position along the line.

        Args:
            values (list): A list of values to find the minimum of
            site_string (str): The symbol of the atom at the start of the line
            neigh_string (str): The symbol of the atom at the end of the line

        results:
            The global minimum of form [line_position, value, frac_position]
        """

        if site_string == neigh_string:
            list_values = list(values)
            # We have the same type of atom on either side. We want to check
            # if they are the same and if they are return a frac of 0.5. This
            # is because usually there will be some slight covalency between
            # atoms of the same type, but they should share the area equally
            symmetric = cls._check_partitioning_line_for_symmetry(list_values)
        else:
            symmetric = False

        # If we found symmetry, we return a global min exactly at the center
        if symmetric:
            # 100 is the index directly at the center of the line
            elf_value = values[100]
            elf_min_frac = 0.5
            global_min = [100, elf_value, elf_min_frac]
        else:
            # We either don't have the same atoms, or the same atoms are not
            # symmetric along the elf.
            # minima function gives all local minima along the values
            minima = cls.find_minimum(values)
            # maxima = find_maximum(values)

            # then we grab the local minima closest to the midpoint of the values
            global_min = cls.get_closest_extrema_to_center(values, minima)
            # global_max = get_closest_extrema_to_center(values, maxima)

            # If we have a high enough voxel resolution we only want to run the rough
            # interpolation. If that's the case we want to do a polynomial fit here
            # to ensure that we have the correct position
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

    @staticmethod
    def get_voxel_coords_from_min_along_line(
        global_min_frac: float,
        site_voxel_coords: ArrayLike | list,
        neigh_voxel_coords: ArrayLike | list,
    ):
        """
        Gives the voxel position/coords for the minimum along a partitioning line
        between two atoms. The minimum point is where the dividing plane should lie.

        Args:
            global_min_frac (float): The global minimum fraction
            site_voxel_coords (ArrayLike): The voxel coordinates of the site at
                the start of the line.
            neigh_voxel_coords (ArrayLike): The voxel coordinates of the neighbor
                atom at the end of the line.
        """

        # get the vector that points between the site and its neighbor (in vox  coords)
        difference = [b - a for a, b in zip(site_voxel_coords, neigh_voxel_coords)]
        # get the vector that points from the site to the global_min_frac
        min_pos = [x * global_min_frac for x in difference]
        # add the vector components of the site and minimum point together to get
        # the vector pointing directly to the minimum
        min_pos = [(a + b) for a, b in zip(min_pos, site_voxel_coords)]
        return np.array(min_pos)

    def get_unit_vector(self, site_voxel_coords, neigh_voxel_coords):
        """
        Gets the unit vector pointing in the direction between two atom sites.

        Args:
            site_voxel_coord (ArrayLike): The voxel coordinates of an atomic site
            neigh_voxel_coord (ArrayLike): The voxel coordinates of a neighboring
                site
        """
        grid = self.grid.copy()
        # get the positions of the atoms in cartesian coordinates.
        site_cart_coords = grid.get_cart_coords_from_vox(site_voxel_coords)
        real_neigh_voxel_coords = grid.get_cart_coords_from_vox(neigh_voxel_coords)
        # The equation of a plane passing through (x1,y1,z1) with normal vector
        # [a,b,c] is:
        #     a(x-x1) + b(y-y1) + c(z-z1) = 0
        # we want the normal vector to be unit vector because later on we
        # will use this information to get the distance of a voxel from
        # the plane.
        normal_vector = [
            (b - a) for a, b in zip(site_cart_coords, real_neigh_voxel_coords)
        ]
        unit_vector = [(x / np.linalg.norm(normal_vector)) for x in normal_vector]
        return np.array(unit_vector)

    @staticmethod
    def get_plane_sign(
        point: ArrayLike | list,
        plane_vector: ArrayLike | list,
        plane_point: ArrayLike | list,
    ):
        """
        Gets the sign associated with a point compared with a plane.

        Args:
            point (ArrayLike): A point in cartesian coordinates to compare with
                a plane
            plane_vector (ArrayLike): The vector normal to the plane of interest
            plane_point (ArrayLike): A point on the plane of interest

        results:
            The sign of the point compared with the plane and the distance of
            the point to the plane.
        """
        # get all of the points in cartesian coordinates
        x, y, z = plane_point
        a, b, c = plane_vector
        x1, y1, z1 = point
        value_of_plane_equation = a * (x - x1) + b * (y - y1) + c * (z - z1)
        # get the distance of the point from the plane with some allowance of error.
        if value_of_plane_equation > 1e-6:
            return "positive", abs(value_of_plane_equation)
        elif value_of_plane_equation < -1e-6:
            return "negative", abs(value_of_plane_equation)
        else:
            return "zero", abs(value_of_plane_equation)

    def get_distance_to_min(
        self,
        minimum_point: ArrayLike | list,
        site_voxel_coords: ArrayLike | list,
    ):
        """
        Gets the distance from an atom to the minimum point along partitioning line
        between it and another atom.

        Args:
            minimum_point (ArrayLike): A point in cartesian coordinates where
                there is a minimum along a line
            site_voxel_coords (ArrayLike): The voxel coordinates of a site that
                is at one end of the line that the minimum belongs to

        results:
            The distance from the site to the minimum
        """
        grid = self.grid.copy()
        site_cart_coords = grid.get_cart_coords_from_vox(site_voxel_coords)
        distance = sum(
            [(b - a) ** 2 for a, b in zip(site_cart_coords, minimum_point)]
        ) ** (0.5)
        return distance

    def get_elf_ionic_radius(
        self,
        site_index: int,
        method: str = "linear",
        structure: Structure = None,
        site_is_electride: bool = False,
    ):
        """
        This method gets the ELF ionic radius. It interpolates the ELF values
        between a site and it's closest neighbor and returns the distance between
        the atom and the minimum in this line. This has been shown to be very
        similar to the Shannon Crystal Radius, but gives more specific values

        Args:
            site_index (int):
                An integer value referencing an atom in the structure
            method (str):
                Whether to use linear or cubic interpolation
            structure (Structure):
                The structure to use if it is not the same as the one stored
                in the PartitioningToolkit instance
            site_is_electride (bool):
                Whether the site in question is an electride site.
        """
        if structure is None:
            structure = self.grid.structure.copy()
        # get neighbors for all atoms in structure
        all_neighbors = self.get_closest_neighbors(structure)
        # Get neighbors only for requested site
        site_neighbors = all_neighbors[site_index]
        # Get site voxel postion from cartesian coordinates
        site_voxel_coord = self.grid.get_voxel_coords_from_cart(
            structure[site_index].coords
        )

        # Create list to store distances in
        distances = []
        for neigh in site_neighbors:
            if neigh["site"].species_string == "He":
                continue
            # Get neighbor voxel coords and then the line between the sites/voxels
            neigh_voxel_coord = self.grid.get_voxel_coords_from_cart(
                neigh["site"].coords
            )
            elf_positions, elf_values = self.get_partitioning_line(
                site_voxel_coord, neigh_voxel_coord
            )

            # Get site and neighbor strings
            site_string = self.grid.structure[site_index].species_string
            neighbor_string = neigh["site"].species_string
            # Get the min position along the line
            global_min_pos = self.get_line_minimum_as_frac(
                elf_values, site_string, neighbor_string
            )
            min_voxel_coord = self.get_voxel_coords_from_min_along_line(
                global_min_pos[2], site_voxel_coord, neigh_voxel_coord
            )
            min_cart_coord = self.grid.get_cart_coords_from_vox(min_voxel_coord)
            distance_to_min = self.get_distance_to_min(min_cart_coord, site_voxel_coord)
            distances.append(distance_to_min)
            # print(distance_to_min)

        elf_radius = min(distances)
        return elf_radius

    def get_closest_neighbors(
        self,
        structure: Structure = None,
    ):
        """
        Function for getting the closest neighbors to an atom. Uses the CrystalNN
        class from pymatgen. This is intended to help quickly check for covalency
        in the structure and may eventually be removed.

        Results:
            A dictionary relating atomic sites to pymatgen neighbor objects
        """
        if structure is None:
            structure = self.grid.structure
        c = CrystalNN(search_cutoff=5)
        closest_neighbors = {}
        for i in range(len(structure)):
            _, _, d = c.get_nn_data(structure, n=i)
            biggest = max(d)
            closest_neighbors[i] = d[biggest]
        return closest_neighbors

    def get_set_number_of_neighbors(self, neighbor_num: int = 26):
        """
        Function for getting the closest neighbors. This is necessary for partitioning
        because the CrystalNN function from pymatgen will not always find the
        correct set of atoms needed to create a full partitioning set. We default
        to 26, but if this is not large enough we automatically increase the amount.

        Args:
            neighbor_num (int): The number of nearest neighbors to find

        Results:
            A list of relating an atoms index to its  neighbors.

        """
        structure = self.grid.structure.copy()
        print(structure)
        # Get all possible neighbor atoms for each atom within 15 angstroms
        all_neighbors = structure.get_all_neighbors(15)
        neighbors = []
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

            site_df = site_df.iloc[0:neighbor_num]

            # Add the neighbors as a list to the df
            neighbors.append(site_df["neighbor"].to_list())
        return neighbors

    @classmethod
    def check_bond_for_covalency(
        cls,
        values: list,
    ):
        """
        Checks for covalent/metallic behavior along a bond. This is done by comparing
        the closest local maximum and minimum to the center of the bond. If the
        maximum is closer, the bond is considered to have some covalent behavior.

        Args:
            values (list): The list of values to check along

        Returns:
            True if the bond has covalent behavior and False if not.
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
        minima = cls.find_minimum(values)
        maxima = cls.find_maximum(values)

        # then we grab the local minima closest to the midpoint of the values
        global_min = cls.get_closest_extrema_to_center(values, minima)
        global_max = cls.get_closest_extrema_to_center(values, maxima)

        # get the distance from the minimum and maximum to the center. The position
        # of the extrema is stored in the first index of the extrema list
        min_dist = abs(midpoint - global_min[0])
        max_dist = abs(midpoint - global_max[0])

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
            if min_elf > max_elf / 2:
                return True
            else:
                return False

    def check_closest_neighbor_for_same_type(
        self,
        closest_neighbors: dict,
    ):
        """
        This function checks indirectly for covalency by checking if an atom's
        closest neighbor is an atom of the same type. This suggests that the
        atoms are covalently bonded. This is to account for the fact that in the
        check_structure_for_covalency method, we skip any atom pairs that are the
        same since they are likely to return as covalent regardless of how far apart
        they are.

        Args:
            closest_neighbors (dict): A dictionary relating sites to pymatgen
                Neigh objects determined from CrystalNN
        Returns:
            Nothing
        """
        structure = self.grid.structure
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
                # check that the neighbors are the same species
                if neigh["site"].specie == specie:
                    same_atom_distances.append(math.dist(site_coords, neigh_coords))
            closest_atom_dist = min(site_distances)
            # find the closest atom of the same type. Sometimes this doesn't exist
            # in the nearest neighbors set so we set this to a large distance.
            try:
                closest_same_atom_dist = min(same_atom_distances)
            except:
                closest_same_atom_dist = 10
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
                partition peaks in the ELF from covalency, though this will hopefully 
                be implemented in a future version of the algorithm.
                
                You can ignore covalency by setting check_covalency = False. Don't
                be surprised if the results are weird though!
                """
            )

    def check_structure_for_covalency(self, closest_neighbors):
        """
        This function is designed to check for covalency along the bonds from each
        atom to its nearest neighbors. The NN are defined by Pymatgen's CrystalNN
        function and covalency is described as a maximum in the ELF that is closer
        to the center of the bond than any minimum.

        Args:
            closest_neighbors (dict): A dictionary relating sites to pymatgen
                Neigh objects determined from CrystalNN

        Returns:
            Nothing
        """
        grid = self.grid.copy()
        structure = grid.structure
        for site_index, neighs in closest_neighbors.items():
            # get voxel position from fractional site
            site_voxel_coord = grid.get_voxel_coords_from_index(site_index)
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

                neigh_voxel_coord = grid.get_voxel_coords_from_neigh_CrystalNN(neigh)
                values = self.get_partitioning_line(
                    site_voxel_coord, neigh_voxel_coord
                )[1]
                # smooth line
                # smoothed_values = savgol_filter(values,20,3)

                # Now we check for any strong covalency in the bond as in the current version
                # of BadELF, this will break the partitioning scheme
                if self.check_bond_for_covalency(values) is True:
                    # report which atoms the bond was found between

                    # import matplotlib.pyplot as plt
                    # plt.plot(smoothed_values)
                    raise Exception(
                        f"""
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
                        
                        The bond was found between {site_species} and {neigh_species}.
                        You can ignore covalency by setting check_covalency = False. Don't
                        be surprised if the results are weird though!
                        """
                    )

    def get_site_neighbor_results(
        self,
        site_index: int,
        neigh,
    ):
        """
        Function for getting the line, plane, and other information between a site
        and neighbor.

        Args:
            site_index (int): The site index of an atom
            neigh (Neigh): A pymatgen neighbor object from the structure.get_neighbors
                method

        results:
            A dictionary containing information about a site neighbor pair.

        """
        grid = self.grid.copy()

        site_voxel_coord = grid.get_voxel_coords_from_index(site_index)
        neigh_voxel_coord = grid.get_voxel_coords_from_neigh(neigh)

        # we need a straight line between these two points.  get list of all ELF values
        elf_positions, elf_values = self.get_partitioning_line(
            site_voxel_coord, neigh_voxel_coord
        )

        # find the minimum position and value along the elf_line
        # the third element is the fractional position, measured from site_voxel_coord
        site_string = grid.structure[site_index].species_string
        neighbor_string = neigh.species_string
        elf_min_index, elf_min_value, elf_min_frac = self.get_line_minimum_as_frac(
            elf_values,
            site_string,
            neighbor_string,
        )

        # convert the minimum in the ELF back into a position in the voxel grid
        elf_min_vox = self.get_voxel_coords_from_min_along_line(
            elf_min_frac, site_voxel_coord, neigh_voxel_coord
        )

        # a point and normal vector describe a plane
        # a(x-x1) + b(y-y1) + c(z-z1) = 0
        # a,b,c is the normal vecotr, x1,y1,z1 is the point

        # convert this voxel grid_pos back into the real_space
        plane_point = grid.get_cart_coords_from_vox(elf_min_vox)

        # get the plane perpendicular to the position.
        plane_vector = self.get_unit_vector(site_voxel_coord, neigh_voxel_coord)

        # it is also helpful to know the distance of the minimum from the site
        distance = self.get_distance_to_min(plane_point, site_voxel_coord)
        return [
            site_index,
            site_voxel_coord,
            neigh,
            neigh_voxel_coord,
            plane_point,
            plane_vector,
            distance,
            elf_positions,
            elf_values,
            elf_min_index,
            elf_min_value,
            elf_min_frac,
            elf_min_vox,
        ]

    @staticmethod
    def get_plane_equation(
        plane_point: ArrayLike | list,
        plane_vector: ArrayLike | list,
    ):
        """
        Gets the equation of a plane from a vector normal to the plane and a
        point on the plane

        Args:
            plane_point (ArrayLike): A point on the plane
            plane_vector (ArrayLike): A vector perpendicular to the plane

        Returns:
            The four plane equation coefficients
        """
        x0, y0, z0 = plane_point
        a, b, c = plane_vector
        d = a * x0 + b * y0 + c * z0
        return a, b, c, d

    @classmethod
    def find_intersection_point(
        cls,
        plane1: ArrayLike | list,
        plane2: ArrayLike | list,
        plane3: ArrayLike | list,
    ):
        """
        Finds the point at which three planes intersect if it exists

        Args:
            plane1 (ArrayLike): A plane of form {"point": point, "vector": vector}
            plane2 (ArrayLike): A plane of form {"point": point, "vector": vector}
            plane3 (ArrayLike): A plane of form {"point": point, "vector": vector}

        Returns:
            The point at which the planes intersect as an array
        """

        a1, b1, c1, d1 = cls.get_plane_equation(plane1["point"], plane1["vector"])
        a2, b2, c2, d2 = cls.get_plane_equation(plane2["point"], plane2["vector"])
        a3, b3, c3, d3 = cls.get_plane_equation(plane3["point"], plane3["vector"])

        A = np.array([[a1, b1, c1], [a2, b2, c2], [a3, b3, c3]])
        b = np.array([d1, d2, d3])

        # Solve the system of equations
        intersection_point = np.linalg.solve(A, b)

        return intersection_point

    @classmethod
    def get_important_planes(cls, planes: list):
        """
        Gets a list of planes that make up a 3D polyhedral.

        Args:
            planes (list): The list of planes to check

        Returns:
            A list of plane intercepts and a list of important planes with form
            {"point": point, "vector": vector}
        """
        # create list for points where planes intersect and for important planes
        intercepts = []
        important_planes = []
        # iterate through each set of 3 planes
        for combination in combinations(planes, 3):
            # try to find an intersection point. We do a try except because if two
            # of the planes are parallel there wont be an intersect point
            try:
                intercept = cls.find_intersection_point(
                    combination[0], combination[1], combination[2]
                )
            except:
                continue

            # Check if the points are one or within the convex shape defined by the
            # planes. Assume this is true at first
            important_intercept = True
            # Check each plane versus the intercept point. If we plug the point into
            # the plane equation it should return as 0 or positive if it is within the
            # shape?
            for plane in planes:
                sign, dist = cls.get_plane_sign(
                    intercept, plane["vector"], plane["point"]
                )
                if sign in ["positive", "zero"]:
                    pass
                else:
                    important_intercept = False
                    break
            # If the point is bound by all planes, it is an important intercept.
            # append it to our list. Also append any new important planes
            if important_intercept:
                intercepts.append(intercept)
                for plane in combination:
                    point = plane["point"]
                    vector = plane["vector"]
                    repeat_plane = False
                    # check if plane already exists in list
                    for plane1 in important_planes:
                        point1 = plane1["point"]
                        vector1 = plane1["vector"]

                        # Check if these planes have the same point and vector. If
                        # they do, indicate that this is a repeate plane
                        if np.array_equal(point, point1) and np.array_equal(
                            vector, vector1
                        ):
                            repeat_plane = True
                            break
                    # If this isn't a repeat plane, add it to our important planes list
                    if not repeat_plane:
                        important_planes.append(plane)
                    # important_plane_points.append(plane["point"])
                    # important_plane_vectors.append(plane["vector"])

            # remove any unimportant planes
            # for point, vector in zip(important_plane_points, important_plane_vectors):
            #     for point1, vector1

        return intercepts, important_planes

    def get_partitioning(
        self,
        neighbors: list = None,
        check_for_covalency: bool = True,
    ):
        """
        Gets the partitioning planes for each atom.

        Args:
            neighbors (list):
                A list of neighbors from pymagten's structure.get_neighbors
                method
            check_for_covalency (bool):
                Whether to check the structure for signs of covalency. This can
                be turned off, but it may give strange results!

        Returns:
            A dictionary where the keys are site indices and the values
            are neighbor dictionaries containing information on the partitioning
            planes.
        """
        if check_for_covalency:
            closest_neighbors = self.get_closest_neighbors()
            self.check_structure_for_covalency(closest_neighbors)
            self.check_closest_neighbor_for_same_type(closest_neighbors)

        if neighbors is None:
            neighbors = self.get_set_number_of_neighbors()
        # self.grid.regrid()
        # structure = grid.structure
        # grid_data = grid.total
        # Now we want to find the minimum in the ELF between the atom and each of its
        # neighbors and the vector between them. This will define a plane seperating
        # the atom from its neighbor.

        # iterate through each site in the structure
        partition_results = []
        columns = [
            "site_index",
            "site_voxel_coord",
            "neigh",
            "neigh_voxel_coord",
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

        # look at each atom neighbor pair for the closest 26 neighbors

        for site_index, neighs in enumerate(neighbors):
            # create a variable indicating that the number of neighbors we've set
            # is enough
            number_of_neighbors = len(neighs)
            enough_neighbors = False

            # create df for each site
            site_df = pd.DataFrame(columns=columns)
            # get voxel position from fractional site
            # site_voxel_coord = grid.get_voxel_coords_from_index(site_index)
            # site_voxel_coord_real = get_real_from_vox(site_voxel_coord, lattice)
            # iterate through each neighbor to the site

            while enough_neighbors is False:
                # For each neighbor, get the plane seperating it from our site and
                # add the info to the site_df
                for i, neigh in enumerate(neighs):
                    site_df.loc[len(site_df)] = self.get_site_neighbor_results(
                        site_index,
                        neigh,
                    )

                # Get list of planes for each atom. The planes are stored as a dictionary
                planes = [
                    {"point": i, "vector": j}
                    for i, j in zip(site_df["plane_point"], site_df["plane_vector"])
                ]
                # get the important planes
                intercepts, important_planes = self.get_important_planes(planes)

                # Create a list to store the final set of neighbors
                important_neighs = pd.DataFrame(columns=columns)
                for [index, row] in site_df.iterrows():
                    # get the associated point and vector for the partitioning plane in
                    # this neighbor.
                    plane_point = np.array(row["plane_point"])
                    plane_vector = np.array(row["plane_vector"])
                    # Check if this plane exists in our list of important planes. If it
                    # does than we'll add this row to our important partitioning planes
                    # list
                    for plane in important_planes:
                        point = plane["point"]
                        vector = plane["vector"]
                        if np.array_equal(plane_point, point) and np.array_equal(
                            plane_vector, vector
                        ):
                            important_neighs.loc[len(important_neighs)] = row

                # Check how many neighbors were found for this site. If it is the
                # same as the maximum number that could of been found, we want to
                # increase the possible number. We increase the desired neighbors by
                # 25 and get the new set of neighbors. Otherwise, we have an
                # appropriate number of neighbors and we add the results to our
                # partitioning results.
                if len(important_neighs) == number_of_neighbors:
                    number_of_neighbors += 25
                    new_neighbors = self.get_set_number_of_neighbors(
                        number_of_neighbors
                    )
                    neighs = new_neighbors[site_index]

                else:
                    enough_neighbors = True
                    partition_results.append(important_neighs)

        # Get results as a dictionary
        # !!! Create a PartitioningResults class to make access easier
        results = {}
        for site_index, site_df in enumerate(partition_results):
            neigh_dict = {}
            for neigh_row in site_df.iterrows():
                # convert dataframe row into a dictionary
                site_neigh_dict = {}
                site_neigh_dict["vox_site"] = neigh_row[1]["site_voxel_coord"]
                site_neigh_dict["vox_neigh"] = neigh_row[1]["neigh_voxel_coord"]
                site_neigh_dict["value_elf"] = neigh_row[1]["elf_min_value"]
                site_neigh_dict["pos_elf_frac"] = neigh_row[1]["elf_min_frac"]
                site_neigh_dict["vox_min_point"] = neigh_row[1]["elf_min_vox"]
                site_neigh_dict["real_min_point"] = neigh_row[1]["plane_point"]
                site_neigh_dict["normal_vector"] = neigh_row[1]["plane_vector"]
                site_neigh_dict["sign"] = "negative"
                site_neigh_dict["radius"] = neigh_row[1]["distance"]
                site_neigh_dict["neigh"] = neigh_row[1]["neigh"]
                # site_neigh_dict["elf_line"] = smoothed_line
                site_neigh_dict["elf_line"] = neigh_row[1]["elf_values_rough"]
                # adding some results for testing
                site_neigh_dict["neigh_index"] = neigh_row[1]["neigh"].index
                # site_neigh_dict["neigh_distance"] = math.dist(real_site_point, real_neigh_point)

                # add row dictionary to neighbor dictionary
                neigh_dict[neigh_row[0]] = site_neigh_dict

            # add the neighbor dictionary to the results dictionary
            results[site_index] = neigh_dict
        return results

    def plot_partitioning_results(
        self,
        partition_results: dict = None,
    ):
        """
        Plots the unit cell and partitioning planes from the partitioning
        results.

        Args:
            partition_results (dict): The results from running the partitioning
                algorithm
        """
        if partition_results is None:
            partition_results = self.get_partitioning()

        # Create a matplotlib plot
        import matplotlib
        import matplotlib.pyplot as plt

        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")

        # Get the vertices of the polygons formed by the partitioning around
        # each atom
        atoms_polygon_nodes = {}
        for site_index, neighs in partition_results.items():
            planes = []
            for neigh in neighs.values():
                plane_point = neigh["real_min_point"]
                plane_vector = neigh["normal_vector"]
                planes.append({"point": plane_point, "vector": plane_vector})
            intercepts, planes = self.get_important_planes(planes)
            atoms_polygon_nodes[site_index] = intercepts

        # get the structure and species
        structure = self.grid.structure
        species = structure.symbol_set

        # plot the unit cell
        self.grid._plot_unit_cell(ax, fig)

        # get a color map to match all same atoms to the same color
        color_map = matplotlib.colormaps.get_cmap("tab10")

        # go through each atom species, set the unique color
        for i, specie in enumerate(species):
            color = color_map(i)
            site_indices = structure.indices_from_symbol(specie)
            # for each site, loop through and plot the surfaces.
            for site in site_indices:
                hull = ConvexHull(atoms_polygon_nodes[site])
                triangles = hull.simplices

                x = []
                y = []
                z = []
                for point in atoms_polygon_nodes[site]:
                    x.append(point[0])
                    y.append(point[1])
                    z.append(point[2])

                ax.plot_trisurf(x, y, z, triangles=triangles, color=color)
