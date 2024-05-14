# -*- coding: utf-8 -*-

import logging
import math
import warnings
from functools import cached_property
from itertools import combinations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from pybader.interface import Bader
from pymatgen.analysis.local_env import CrystalNN
from scipy.interpolate import RegularGridInterpolator
from scipy.signal import savgol_filter
from scipy.spatial import ConvexHull
from tqdm import tqdm

from simmate.apps.badelf.core.grid import Grid
from simmate.toolkit import Structure


class PartitioningToolkit:
    """
    A set of tools for aiding in partitioning a 3D voxel grid. These tools make
    up the basis for the partitioning utilized in BadELF and the related
    VoronELF algorithms.

    Args:
        grid (Grid):
            A BadELF app Grid type object.
        pybader (Bader):
            A bader Bader type object.
    """

    def __init__(self, grid: Grid, bader: Bader):
        self.grid = grid.copy()
        self.bader = bader

    def get_partitioning_line_from_voxels(
        self,
        site_voxel_coord: ArrayLike | list,
        neigh_voxel_coord: ArrayLike | list,
        method: str = "linear",
        steps: int = 200,  #!!! This should be set dynamically in the future
    ):
        """
        Finds a line of voxel positions between two atom sites and then finds the value
        of the partitioning grid at each of these positions. The values are found
        using an interpolation function defined using SciPy's RegularGridInterpeter.

        Args:
            site_voxel_coord (ArrayLike):
                The voxel coordinates of an atomic site
            neigh_voxel_coord (ArrayLike):
                The voxel coordinates of a neighboring
                site
            method (str):
                The method of interpolation. 'cubic' is more rigorous
                than 'linear'
            steps (int):
                The number of voxel coordinates to interpolate. Default is 200

        Results:
            A list with 200 pairs of voxel coordinates and data values along
            a line between two positions.
        """
        grid_data = self.grid.copy().total
        label_data = self.bader.atoms_volumes
        slope = [b - a for a, b in zip(site_voxel_coord, neigh_voxel_coord)]
        slope_increment = [float(x) / steps for x in slope]

        # get a list of points along the connecting line. First add the original
        # site
        position = site_voxel_coord
        line = [[round(float(a % b), 12) for a, b in zip(position, grid_data.shape)]]
        for i in range(steps):
            # move position by slope_increment
            position = [float(a + b) for a, b in zip(position, slope_increment)]

            # Wrap values back into cell
            # We must do (a-1) to shift the voxel index (1 to grid_max+1) onto a
            # normal grid, (0 to grid_max), then do the wrapping function (%), then
            # shift back onto the VASP voxel index.
            position = [
                round(float(a % b), 12) for a, b in zip(position, grid_data.shape)
            ]

            line.append(position)

        # The partitioning uses a padded grid and grid interpolation to find the
        # location of dividing planes.
        padded_grid_data = np.pad(grid_data, 1, mode="wrap")
        padded_label_data = np.pad(label_data, 1, mode="wrap")

        # interpolate grid to find values that lie between voxels. This is done
        # with a cruder interpolation here and then the area close to the minimum
        # is examened more closely with a more rigorous interpolation in
        # get_line_frac_min
        a, b, c = self.grid.get_padded_grid_axes(1)
        fn = RegularGridInterpolator((a, b, c), padded_grid_data, method=method)
        fn_label = RegularGridInterpolator((a, b, c), padded_label_data, "nearest")
        # get a list of the ELF values along the line
        values = []
        label_values = []

        for pos in line:
            adjusted_pos = [x + 1 for x in pos]
            value = float(fn(adjusted_pos))
            label_value = int(fn_label(adjusted_pos))
            values.append(value)
            label_values.append(label_value)

        return line, values, label_values

    def get_partitioning_line_from_indices(
        self, i: int, j: int, method: str = "linear"
    ):
        """
        Gets the voxel positions and elf values for points between two sites in
        the structure.

        Args:
            i (int):
                index of first site in the structure
            j (int):
                index of second site in the structure
            method (str):
                The method of interpolation. 'cubic' is more rigorous
                than 'linear'

        Returns:
        - Two lists, one of positions in voxel coordinates and another of elf
        values
        """
        grid = self.grid.copy()
        site_voxel_coord = grid.get_voxel_coords_from_index(i)
        neigh_voxel_coord = grid.get_voxel_coords_from_index(j)
        return self.get_partitioning_line_from_voxels(
            site_voxel_coord, neigh_voxel_coord, method=method
        )

    def get_partitioning_line_from_cart_coords(
        self,
        site_cart_coords: ArrayLike | list,
        neigh_cart_coords: ArrayLike | list,
        method: str = "linear",
    ):
        """
        Gets the voxel positions and elf values for points between two sites in
        the structure given as cartesian coordinates. This method can also be
        used to find the values in the ELF between two arbitrary points in the
        structure.

        Args:
            site_cart_coords (ArrayLike):
                cartesian coordinates of a site in the structure
            neigh_cart_coords (ArrayLike):
                cartesian coordinates of a second site in the structure
            method (str):
                The method of interpolation. 'cubic' is more rigorous
                than 'linear'

        Returns:
            Two lists, one of positions in voxel coordinates and another of elf
            values
        """
        grid = self.grid.copy()
        site_voxel_coord = grid.get_voxel_coords_from_cart(site_cart_coords)
        neigh_voxel_coord = grid.get_voxel_coords_from_cart(neigh_cart_coords)
        return self.get_partitioning_line_from_voxels(
            site_voxel_coord, neigh_voxel_coord, method=method
        )

    @staticmethod
    def _check_partitioning_line_for_symmetry(values: list, tolerance: float = 10):
        """
        Check if the values are roughly symmetric. Checks each value versus
        the equivalent value of the other half to see if they are within the
        requested percent diff.

        Args:
            values (list):
                List of numeric values
            tolerance (float):
                Tolerance level for symmetry check in percents.

        Returns:
            True if roughly symmetric, False otherwise
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
            perc_diff = abs((val1 - val2) / (val1 + val2)) * 100
            if perc_diff > tolerance:
                return False

        return True

    @staticmethod
    def find_minimum(values: list | ArrayLike):
        """
        Finds the local minima in a list of values and returns the index and value
        at each as a list of form [[min_index1, min_value1], [min_index2, min_value2], ...]

        Args:
            values (list):
                The list of values to find the minima of

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
            values (list):
                The list of values to find the minima of

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
            values (list):
                A list of values
            extrema (list):
                A list of extrema of form [index, value]

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

    def get_line_minimum_as_frac(
        self,
        positions: list,
        values: list | ArrayLike,
        labels: list | ArrayLike,
        site_index: int,
        neigh_index: int,
    ):
        """
        Finds the minimum point of a list of values along a line, then returns the
        fractional position of this values position along the line.

        Args:
            positions (list):
                A list of positions given as voxel coordinates along the line
                of interest
            values (list):
                A list of values to find the minimum of
            site_index (int):
                The index of the atom
            neigh_index (int):
                The index of the neighboring atom

        results:
            The global minimum of form [line_position, value, frac_position]
        """
        # In some cases I have found that linear interpolation near electride
        # sites is wavy resulting in many maxima and causing problems with the
        # partitioning. To deal with this I put the linear values through a
        # savgol filter
        values = savgol_filter(values, 20, 3)

        site_equiv = self.grid.equivalent_atoms[site_index]
        neigh_equiv = self.grid.equivalent_atoms[neigh_index]
        # get the string for the site and neigh. During the electride dimensionality
        # search this can throw an error so we add a try/except clause here.
        try:
            site_string = self.grid.structure[site_equiv].species_string
            neigh_string = self.grid.structure[neigh_equiv].species_string
        except:
            site_string = "He"
            neigh_string = "H"

        if site_equiv == neigh_equiv:
            # We have an atom bonded to another atom that is symmetrically equivalent
            # so the resulting elf line will be equivalent
            symmetric = True
        elif site_string == neigh_string:
            list_values = list(values)
            # We have two atoms of the same type that are not found as symmetric
            # by pymatgen. However, it is still likely that the ELF between the
            # two atoms is symmetric which can easily result in a covalent like
            # behavior. To handle this, we check if the line is symmetric and
            # if it is we place the frac at exactly the middle
            symmetric = self._check_partitioning_line_for_symmetry(list_values)
        else:
            symmetric = False

        # Now if our line is symmetric, we place our partitioning exactly at
        # the middle of the line. Otherwise we interpolate to find where to
        # place the line.
        if symmetric:
            elf_value = values[100]
            elf_min_frac = 0.5
            global_min = [100, elf_value, elf_min_frac]
        else:
            # If the only assignments in our line are for the two atoms involved
            # we guess that our initial partitioning frac will be at the furthest
            # point still labeled as belonging to the site
            if np.all(np.isin(labels, [site_index, neigh_index])):
                elf_min_index = np.where(np.array(labels) == site_index)[0].max()
                extrema = "min"
            else:
                # There is at least some section of the line that is assigned to an
                # atom not in the bond. We want to assign the fraction as being at
                # the maximum of this unrelated area. However, sometimes I've
                # found that there is no maximum in the range of this area which
                # causes the assignment to be placed very far from what is reasonable.
                # to handle this we check if there is a maximum in the unrelated area
                # and if not we assign as above.
                # There is a potential for a bug where a very small maximum is
                # found using linear interpolation that is then removed with
                # cubic interpolation. This actually happened with Ba2N. To deal
                # with this, I've added a cutoff where the maximum must be at
                # least 0.01 greater than the absolute minimum of the values
                maxima = self.find_maximum(values)
                unrelated_indices = np.where(
                    ~np.isin(labels, [site_index, neigh_index])
                )
                new_maxima = []
                for maximum in maxima:
                    if (
                        np.isin(maximum[0], unrelated_indices)
                        and (maximum[1] - min(values)) > 0.01
                    ):
                        new_maxima.append(maximum)
                if len(new_maxima) > 0:
                    elf_min_index = self.get_closest_extrema_to_center(
                        values, new_maxima
                    )[0]
                    extrema = "max"
                else:
                    elf_min_index = np.where(np.array(labels) == site_index)[0].max()
                    extrema = "min"

            global_min = self._refine_line_part_frac(
                positions=positions,
                elf_min_index=elf_min_index,
                extrema=extrema,
            )

        return global_min

    def _refine_line_part_frac(
        self,
        positions: list,
        elf_min_index: int,
        extrema: str,
    ):
        """
        Refines the location of the minimum along an ELF line between two sites.
        To do this, the initial estimate from a linear interpolation of the line
        is used and a cubic interpolation is used in a smaller area around the
        estimated point. The sampled area is adjusted if it is found to not be
        centered on the new more accurate minimum.

        Args:
            positions (list):
                A list of positions given as voxel coordinates along the line
                of interest
            elf_min_index (int):
                The index along the line at which the linear interpolation estimated
                the minimum.
            extrema (str):
                Which type of extrema to refine. Either max or min.

        Returns:
            The global minimum of form [line_position, value, frac_position]
        """
        amount_to_pad = 10
        grid = self.grid.copy()
        padded = np.pad(grid.total, amount_to_pad, mode="wrap")

        # interpolate the grid with a more rigorous method to find more exact value
        # for the plane.
        a, b, c = grid.get_padded_grid_axes(10)
        fn = RegularGridInterpolator((a, b, c), padded, method="cubic")

        # create variables for if the line needs to be shifted from what the
        # rough partitioning found
        centered = False
        amount_to_shift = 0
        attempts = 0

        while centered == False:
            if attempts == 5:
                break
            else:
                attempts += 1
                # If the position wasn't centered previously, we need to shift
                # the index
                elf_min_index = elf_min_index + amount_to_shift
                line_section = positions[elf_min_index - 3 : elf_min_index + 4]
                line_section_x = [
                    i for i in range(elf_min_index - 3, elf_min_index + 4)
                ]

                values_fine = []
                # Get the list of values from the interpolated grid
                for pos in line_section:
                    new_pos = [i + amount_to_pad for i in pos]
                    value_fine = float(fn(new_pos))
                    values_fine.append(value_fine)

                # Find the minimum value of this line as well as the index for this value's
                # position.
                try:
                    if extrema == "min":
                        minimum_value = min(values_fine)
                    elif extrema == "max":
                        minimum_value = max(values_fine)
                except:
                    attempts = 5
                    continue
                min_pos = values_fine.index(minimum_value)  # + global_min_pos[0]-5

                if min_pos == 4:
                    # Our line is centered and we can move on
                    centered = True
                else:
                    # Our line is not centered and we need to adjust it
                    amount_to_shift = min_pos - 4

        if not centered:
            # The above sometimes fails because the linear fitting gives a guess
            # for the minimum that isn't close. To handle this we treat these
            # situations rigorously
            values = []

            # Get the ELF value for every position in the line.
            for pos in positions:
                new_pos = [i + amount_to_pad for i in pos]
                value = float(fn(new_pos))
                values.append(value)

            # Get a list of all of the minima along the line
            if extrema == "min":
                minima = self.find_minimum(values)
            elif extrema == "max":
                minima = self.find_maximum(values)

            # then we grab the local minima closest to the midpoint of the line
            global_min = self.get_closest_extrema_to_center(values, minima)

            # now we want a small section of the line surrounding the minimum
            values_fine = values[global_min[0] - 3 : global_min[0] + 4]
            line_section_x = [i for i in range(global_min[0] - 3, global_min[0] + 4)]

        # now that we've found the values surrounding the minimum of our line,
        # we can fit these values to a 2nd degree polynomial and solve for its
        # minimum point
        try:
            d, e, f = np.polyfit(line_section_x, values_fine, 2)
            x = -e / (2 * d)
            elf_min_index_new = x
            elf_min_value_new = np.polyval(np.array([d, e, f]), x)
            elf_min_frac_new = elf_min_index_new / (len(positions) - 1)
        except:
            breakpoint()

        return [elf_min_index_new, elf_min_value_new, elf_min_frac_new]

    @staticmethod
    def get_plane_sign(
        point: ArrayLike | list,
        plane_vector: ArrayLike | list,
        plane_point: ArrayLike | list,
    ):
        """
        Gets the sign associated with a point compared with a plane.

        Args:
            point (ArrayLike):
                A point in cartesian coordinates to compare with a plane
            plane_vector (ArrayLike):
                The vector normal to the plane of interest
            plane_point (ArrayLike):
                A point on the plane of interest

        Returns:
            The sign of the point compared with the plane and the distance of
            the point to the plane.
        """
        # get all of the points in cartesian coordinates
        x, y, z = plane_point
        a, b, c = plane_vector
        x1, y1, z1 = point
        value_of_plane_equation = round(
            (a * (x - x1) + b * (y - y1) + c * (z - z1)), 12
        )
        # get the distance of the point from the plane with some allowance of error.
        if value_of_plane_equation > 0:
            return "positive", value_of_plane_equation
        elif value_of_plane_equation < 0:
            return "negative", value_of_plane_equation
        else:
            return "zero", value_of_plane_equation

    def get_elf_ionic_radius(
        self,
        site_index: int,
    ):
        """
        This method gets the ELF ionic radius. It interpolates the ELF values
        between a site and it's closest neighbor and returns the distance between
        the atom and the minimum in this line. This has been shown to be very
        similar to the Shannon Crystal Radius, but gives more specific values

        Args:
            site_index (int):
                An integer value referencing an atom in the structure

        Returns:
            The distance the ELF ionic radius of the site
        """
        # get closest neighbor for the given site

        neighbors = self.all_site_neighbor_pairs
        # get only this sites dataframe
        site_df = neighbors.loc[neighbors["site_index"] == site_index]
        site_df.reset_index(inplace=True, drop=True)

        # Get to the closest neighbor to the site that isn't a He dummy atom
        for i, row in site_df.iterrows():
            site_cart_coords = row["site_coords"]
            neigh_cart_coords = row["neigh_coords"]
            neighbor_string = row["neigh_symbol"]
            if neighbor_string != "He":
                bond_dist = row["dist"]
                break

        (
            elf_positions,
            elf_values,
            label_values,
        ) = self.get_partitioning_line_from_cart_coords(
            site_cart_coords,
            neigh_cart_coords,
        )

        elf_min_index = np.where(np.array(label_values) == site_index)[0].max()
        refined_index = self._refine_line_part_frac(elf_positions, elf_min_index, "min")
        distance_to_min = refined_index[2] * bond_dist

        return distance_to_min

    @staticmethod
    def _get_vector_plane_intersection(
        point0: ArrayLike | list,
        point1: ArrayLike | list,
        plane_point: ArrayLike | list,
        plane_vector: ArrayLike | list,
        allow_point_intercept: bool = False,
    ):
        """
        Takes in two points and the point/vector defining a plane and returns
        the point where the line segment and plane intersect (if it exists)

        Args:
            point0 (ArrayLike): The first point of a line segment
            point1 (ArrayLike): The second point of a line segment
            plane_point (ArrayLike): A point on the plane
            plane_vector (ArrayLike): The vector normal to the plane
            allow_point_intercept (bool): Whether to count a point at the end
                of the line segment touching the plane as an intercept.

        Returns:
            The point where the line segment intersects the plane or None if
            there is no intersection.
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

    def _reduce_planes_quick(
        self,
        plane_points: ArrayLike | list,
        plane_vectors: ArrayLike | list,
        dists: ArrayLike | list,
        site_cart_coord: ArrayLike | list,
    ):
        """
        Reduces a set of planes around a site by checking if the line between
        the site and each plane is intersected by other planes.

        Args:
            plane_points (ArrayLike):
                An array of points on planes of shape (N,3)
            plane_vectors (ArrayLike):
                An array of plane vertices of shape (N,3)
            dists (ArrayLike):
                An array of distances from the site to the planes of shape (N)
            site_cart_coords (ArrayLike):
                The cartesian coordinates of the site

        Returns:
            Three arrays corresponding to the indices of the reduced planes,
            the reduced plane's points and the reduced plane's vectors
        """
        # convert to arrays if not already
        all_plane_points = np.array(plane_points)
        all_plane_vectors = np.array(plane_vectors)
        dists = np.array(dists)
        unique_dists = list(set(dists))
        # Get initial set of planes
        initial_indices = np.where(dists == unique_dists[0])[0]
        # Create arrays of plane points and vectors
        reduced_plane_points = all_plane_points[initial_indices]
        reduced_plane_vectors = all_plane_vectors[initial_indices]
        reduced_indices = initial_indices.copy()
        # loop over every unique distance. All the planes at this distance are
        # symmetric. Check if they are important by seeing if the line between the
        # atom and the plane point is intersected by any of the existing planes
        for dist in unique_dists[1:]:
            first_index = np.where(dists == dist)[0][0]
            point0 = site_cart_coord
            point1 = all_plane_points[first_index]
            # important_plane = True
            intersects = []
            for i, plane_point in enumerate(reduced_plane_points):
                plane_vector = reduced_plane_vectors[i]
                intersect = self._get_vector_plane_intersection(
                    point0, point1, plane_point, plane_vector
                )
                if intersect is None:
                    pass
                else:
                    # important_plane = False
                    intersects.append(intersect)
                    break
            # if important_plane:
            if len(intersects) < 3:
                indices_to_add = np.where(dists == dist)[0]
                reduced_indices = np.concatenate((reduced_indices, indices_to_add))
                points_to_add = all_plane_points[indices_to_add]
                vectors_to_add = all_plane_vectors[indices_to_add]
                reduced_plane_points = np.concatenate(
                    (reduced_plane_points, points_to_add)
                )
                reduced_plane_vectors = np.concatenate(
                    (reduced_plane_vectors, vectors_to_add)
                )
        return reduced_indices, reduced_plane_points, reduced_plane_vectors

    @cached_property
    def all_site_neighbor_pairs(self):
        """
        A dataframe containing information about all site-neighbor pairs in a
        structure within 15A of each other.
        """
        grid = self.grid
        structure = grid.structure
        # logging.info("Getting all neighboring atoms for each site in structure")
        # Get all neighbors within 15 Angstrom
        nearest_neighbors = structure.get_neighbor_list(15)
        # Get the equivalent atom index for each atom
        equivalent_atoms = grid.equivalent_atoms
        equiv_site_index = equivalent_atoms[nearest_neighbors[0]]
        equiv_neigh_index = equivalent_atoms[nearest_neighbors[1]]
        # Create dataframe with important info about each site/neighbor pair
        site_neigh_pairs = pd.DataFrame()
        # Add sites and neighbors indices
        site_neigh_pairs["site_index"] = nearest_neighbors[0]
        site_neigh_pairs["neigh_index"] = nearest_neighbors[1]
        site_neigh_pairs["equiv_site_index"] = equiv_site_index
        site_neigh_pairs["equiv_neigh_index"] = equiv_neigh_index
        site_neigh_pairs["site_symbol"] = None
        site_neigh_pairs["neigh_symbol"] = None

        site_cart_coords = []
        for site_index, site in enumerate(structure):
            # Add species strings to all site and neighbor indices with given index
            species_string = site.species_string
            site_condition = site_neigh_pairs["site_index"] == site_index
            neigh_condition = site_neigh_pairs["neigh_index"] == site_index
            site_neigh_pairs.loc[site_condition, "site_symbol"] = species_string
            site_neigh_pairs.loc[neigh_condition, "neigh_symbol"] = species_string
            # Get the coordinate for this site index. Create a list of arrays made up
            # of this coordinate and add it to our site coords list
            site_coord = list(site.coords)
            atom_neigh_len = len(site_neigh_pairs.loc[site_condition])
            site_coords_array = np.tile(site_coord, (atom_neigh_len, 1))
            site_cart_coords.extend(site_coords_array)

        # Add the distances for each site-neighbor pair, then round them to 5 decimals
        site_neigh_pairs["dist"] = nearest_neighbors[3]
        site_neigh_pairs["dist"] = site_neigh_pairs["dist"].round(5)
        # Add the site coordinates
        site_neigh_pairs["site_coords"] = site_cart_coords
        # Get the fractional coordinates for each neighbor atom. Then calculate the cartesian coords
        neigh_frac_coords = (
            structure.frac_coords[nearest_neighbors[1]] + nearest_neighbors[2]
        )
        neigh_cart_coords = []
        neigh_cart_coords.extend(
            grid.get_cart_coords_from_frac_full_array(neigh_frac_coords)
        )
        # Add the neighbors cartesian coordinates
        site_neigh_pairs["neigh_coords"] = neigh_cart_coords

        # Create columns for the partitioning fraction and radius
        site_neigh_pairs["partitioning_frac"] = None
        site_neigh_pairs["radius"] = None
        site_neigh_pairs.sort_values(by="dist", inplace=True)

        return site_neigh_pairs

    def get_closest_neighbors(
        self,
        structure: Structure = None,
    ):
        """
        Function for getting the closest neighbors to an atom. Uses the CrystalNN
        class from pymatgen. This is intended to help quickly check for covalency
        in the structure and may eventually be removed.

        Args:
            structure (Structure):
                The structure to get closest neighbors for. Defaults to the
                base structure for this PartitioningToolkit instance

        Returns:
            A dictionary relating atomic sites to pymatgen neighbor objects
        """
        if structure is None:
            structure = self.grid.structure
        c = CrystalNN(search_cutoff=5)
        closest_neighbors = {}
        for i in range(len(structure)):
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", category=UserWarning, module="pymatgen"
                )
                _, _, d = c.get_nn_data(structure, n=i)
            biggest = max(d)
            closest_neighbors[i] = d[biggest]
        return closest_neighbors

    def get_set_number_of_neighbors(self, site_index, neighbor_num: int = 26):
        """
        Function for getting the closest neighbors.

        Args:
            site_index (int):
                The atomic site of interest
            neighbor_num (int):
                The number of nearest neighbors to find

        Results:
            A dataframe relating an atoms index to its  neighbors.

        """
        # Get all possible neighbor atoms for each atom within 15 angstroms
        all_neighbors = self.all_site_neighbor_pairs.copy()
        atom_neighbors = all_neighbors.loc[
            all_neighbors["site_index"] == site_index
        ].copy()
        set_neighbors = atom_neighbors.iloc[:neighbor_num]

        return set_neighbors

    def get_site_neighbor_frac(
        self,
        site_cart_coords: ArrayLike,
        neigh_cart_coords: ArrayLike,
        site_index: int,
        neigh_index: int,
    ):
        """
        Function for getting the fraction of a line betwaeen two sites where
        the ELF is at a minimum.

        Args:
            site_cart_coords (Array | list):
                The cartesian coordinates of the first site.
            neigh_cart_coords (Array | list):
                The cartesian coordinates of the neighboring site.

        Returns:
            The minimum point in the ELF between the two sites.

        """
        grid = self.grid.copy()

        site_voxel_coord = grid.get_voxel_coords_from_cart(site_cart_coords)
        neigh_voxel_coord = grid.get_voxel_coords_from_cart(neigh_cart_coords)

        # we need a straight line between these two points.  get list of all ELF values
        (
            elf_coordinates,
            elf_values,
            label_values,
        ) = self.get_partitioning_line_from_voxels(
            site_voxel_coord, neigh_voxel_coord, method="linear"
        )

        # find the minimum position and value along the elf_line
        # the third element is the fractional position, measured from site_voxel_coord
        elf_min_index, elf_min_value, elf_min_frac = self.get_line_minimum_as_frac(
            elf_coordinates,
            elf_values,
            label_values,
            site_index,
            neigh_index,
        )
        return elf_min_frac

    @staticmethod
    def get_plane_equation(
        plane_point: ArrayLike | list,
        plane_vector: ArrayLike | list,
    ):
        """
        Gets the equation of a plane from a vector normal to the plane and a
        point on the plane

        Args:
            plane_point (ArrayLike):
                A point on the plane
            plane_vector (ArrayLike):
                A vector perpendicular to the plane

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
            plane1 (ArrayLike):
                An Array of length 6 with the first three values representing
                the vector orthogonal to the plane and the second three values
                representing the point on the plane.
            plane2 (ArrayLike):
                An Array of length 6 with the first three values representing
                the vector orthogonal to the plane and the second three values
                representing the point on the plane.
            plane3 (ArrayLike):
                An Array of length 6 with the first three values representing
                the vector orthogonal to the plane and the second three values
                representing the point on the plane.

        Returns:
            The point at which the planes intersect as an array
        """

        a1, b1, c1, d1 = cls.get_plane_equation(plane1[:3], plane1[3:])
        a2, b2, c2, d2 = cls.get_plane_equation(plane2[:3], plane2[3:])
        a3, b3, c3, d3 = cls.get_plane_equation(plane3[:3], plane3[3:])

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
            planes (list):
                The list of planes to check

        Returns:
            A list of plane intercepts and a list of important planes as arrays
            with the first 3 values being the vector and the second three values
            being the point.
        """
        # create list for points where planes intersect
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
            # shape.
            for plane in planes:
                sign, dist = cls.get_plane_sign(
                    point=intercept,
                    plane_vector=plane[3:],
                    plane_point=plane[:3],
                )
                # if sign in ["positive", "zero"]:
                # print(dist)
                if dist >= -1e-5:
                    pass
                else:
                    important_intercept = False
                    # print(dist)
                    break
            # If the point is bound by all planes, it is an important intercept.
            # append it to our list.
            if important_intercept:
                # check if intercept is already in list. If it's not, continue
                # repeat_intercept = any(
                #     np.array_equal(intercept, arr) for arr in intercepts
                # )
                # if not repeat_intercept:
                intercepts.append(intercept)
                for plane in combination:
                    repeat_plane = any(
                        np.array_equal(plane, arr) for arr in important_planes
                    )
                    # If this isn't a repeat plane, add it to our important planes list
                    if not repeat_plane:
                        important_planes.append(plane)

        return intercepts, important_planes

    @cached_property
    def maximum_site_neighbor_pairs(self):
        """
        Finds the maximum list of sites that might contribute to the partitioning
        surface. This is found by considering a small surface made up of planes
        that are definitely on the partitioning surface. A larger surface is
        then constructed by doubling the distance from the atom to each plane
        (the distance to the neighbor atom is used instead if it is larger). Then
        any site inside of this new surface may contribute to the overall surface

        Returns:
            A dataframe of site neighbor pairs with plane information
        """
        # get the structure and a list pointing to the first equivalent atom
        # for each site
        structure = self.grid.structure
        equivalent_atoms = self.grid.equivalent_atoms
        unique_atoms = list(set(equivalent_atoms))
        # get a dataframe containing all site neighbor pairs. We will reduce
        # from here
        all_site_neighbor_pairs = self.all_site_neighbor_pairs
        # Get the site neighbor pairs corresponding to each unique atom in the
        # structure. We only look at unique atoms to avoid a large number of
        # calculations in highly symmetrical structures
        unique_site_dataframes = {}
        for site_index, site in enumerate(structure):
            # check if site is unique
            if site_index in unique_atoms:
                # locate all rows in full site-neighbor pair dataframe where
                # the site matches the one we're looking at
                site_dataframe = all_site_neighbor_pairs.loc[
                    all_site_neighbor_pairs["site_index"] == site_index
                ]
                site_dataframe.reset_index(inplace=True, drop=True)
                # add the reduced dataframe to our list of unique dataframes
                unique_site_dataframes[site_index] = site_dataframe
        # Now we begin reducing the site-neighbor pairs. We will use a small
        # set of planes that enclose the site to check which other sites might
        # potentially contribute to the partitioning surface.
        # We will start with the closest neighbors, calculate the dividing
        # planes and then check if these planes enclose a reasonable space. If
        # not we'll add planes until it does. Once we have our surface planes,
        # we'll calculate which sites are inside of this surface
        logging.info("Calculating maximum set of neighboring atoms")
        atom_potential_planes = {}
        for site_index, site_dataframe in tqdm(
            unique_site_dataframes.items(),
            total=len(unique_site_dataframes),
            ascii="░▒▓",
        ):
            # First we find the unique sets of atom neighbor pairs for this atom.
            unique_site_df = site_dataframe.drop_duplicates(
                subset=["site_symbol", "neigh_symbol", "dist"]
            )
            # create our dataframe for out surface planes
            surface_planes = pd.DataFrame()
            # Now we progressively add more planes by distance from the atom unitl we
            # have a closed surface around the atom.
            for i, row in unique_site_df.iterrows():
                # get the coords of each site and its neighbor for this row
                site_cart_coords = row["site_coords"]
                neigh_cart_coords = row["neigh_coords"]
                # get the site and neighbor symbols
                neigh_index = row["neigh_index"]
                shortest_dist = row["dist"]
                # get fraction along line where the min is located
                frac = self.get_site_neighbor_frac(
                    site_cart_coords,
                    neigh_cart_coords,
                    site_index,
                    neigh_index,
                )
                # Set frac to 2*frac or 1 whichever is larger
                if 2 * frac >= 1:
                    frac = (2 * frac) + 0.1
                else:
                    frac = 1.1
                # get all of the planes at this distance
                planes_at_dist = site_dataframe.loc[
                    site_dataframe["dist"] == shortest_dist
                ].copy()

                # Get the site and neighbor coords in arrays to make calculations easier
                site_coords = np.array(planes_at_dist["site_coords"].to_list())
                neigh_coords = np.array(planes_at_dist["neigh_coords"].to_list())

                # Calculate the plane points and vectors for this set of planes
                vectors = neigh_coords - site_coords
                magnitudes = np.linalg.norm(vectors, axis=1)
                unit_vectors = vectors / magnitudes[:, np.newaxis]
                plane_points = vectors * frac + site_coords
                # Append them to the initial vectors dataframe
                planes_at_dist["frac"] = frac
                planes_at_dist["plane_vectors"] = list(unit_vectors)
                planes_at_dist["plane_points"] = list(plane_points)
                surface_planes = pd.concat([surface_planes, planes_at_dist])
                # Get all of the surface planes so far
                surface_plane_points = np.array(
                    surface_planes["plane_points"].to_list()
                )
                surface_plane_vectors = np.array(
                    surface_planes["plane_vectors"].to_list()
                )
                surface_planes_array = np.concatenate(
                    (surface_plane_points, surface_plane_vectors), axis=1
                )
                # Calculate the points at which the three planes intersect to
                # form a closed polyhedra
                important_vertices, _ = self.get_important_planes(surface_planes_array)
                try:
                    # check if we've enclosed a reasonably sized space. If not
                    # repeat with more planes. Otherwise continue on
                    hull = ConvexHull(important_vertices)
                    volume = hull.volume
                    if volume < 1200:
                        break
                except:
                    continue
            # Now we need to find which atoms are contained in this bound region. We loop
            # over each unique atom-neigh pair. If the neighbor is within the region, it
            # is possible this neighbor and all symmetrically equivalent ones are important
            # to the voronoi surface
            potential_plane_indices = []
            for i, row in unique_site_df.iterrows():
                neigh_cart_coords = row["neigh_coords"]
                dist = row["dist"]
                potential_bounding_plane = True
                # Check each plane versus the intercept point. If we plug the point into
                # the plane equation it should return as 0 or positive if it is within the
                # shape?
                for plane in surface_planes_array:
                    sign, _ = PartitioningToolkit.get_plane_sign(
                        point=neigh_cart_coords,
                        plane_vector=plane[3:],
                        plane_point=plane[:3],
                    )
                    if sign in ["positive", "zero"]:
                        pass
                    else:
                        potential_bounding_plane = False
                        break
                if potential_bounding_plane:
                    # These are potentially important planes. We want to store the indices
                    # So they're easy to find for every identical atom
                    indices = site_dataframe.loc[
                        site_dataframe["dist"] == dist
                    ].index.to_list()
                    potential_plane_indices.extend(indices)

            atom_potential_planes[site_index] = potential_plane_indices

        # Now we get all possible site neighbor pairs in one dataframe, similar
        # to the all_site_neighbor_pairs dataframe but reduced
        possible_site_neigh_pairs = pd.DataFrame()
        for site_index, site in enumerate(structure):
            equivalent_atom = self.grid.equivalent_atoms[site_index]
            plane_indices = atom_potential_planes[equivalent_atom]
            site_dataframe = all_site_neighbor_pairs.loc[
                all_site_neighbor_pairs["site_index"] == site_index
            ].copy()
            site_dataframe.sort_values(by="dist", inplace=True)
            site_dataframe.reset_index(inplace=True, drop=True)
            reduced_site_dataframe = site_dataframe.iloc[plane_indices]
            possible_site_neigh_pairs = pd.concat(
                [possible_site_neigh_pairs, reduced_site_dataframe]
            )
        possible_site_neigh_pairs = self._calculate_partitioning_planes(
            possible_site_neigh_pairs
        )
        return possible_site_neigh_pairs

    def _calculate_partitioning_planes(self, possible_site_neigh_pairs):
        """
        Calculates the plane points and vectors for provided site neighbor pairs.

        Args:
            possible_site_neigh_pairs (pd.DataFrame):
                A dataframe of potential site neighbor pairs. Must have the
                columns "site_coords, "neigh_coords", "site_symbol",
                "neigh_symbol", and "dist".

        Returns:
            A dataframe of site neighbor pairs with plane information
        """
        possible_unique_pairs = possible_site_neigh_pairs.drop_duplicates(
            # subset=["site_symbol", "neigh_symbol", "dist"]
            subset=["equiv_site_index", "equiv_neigh_index", "dist"]
        )

        # calculate fractions along each line in the ELF
        logging.info("Calculating partitioning plane positions from ELF")
        # Get partitioning frac for each unique site_neighbor pair
        for index, row in tqdm(
            possible_unique_pairs.iterrows(),
            total=len(possible_unique_pairs),
            ascii="░▒▓",
        ):
            # Check if we've already found the frac for this row
            if row["partitioning_frac"] is None:
                # get coords of each site and its neighbor
                site_cart_coords = row["site_coords"]
                # site_voxel_coords = grid.get_voxel_coords_from_cart(site_cart_coords)
                neigh_cart_coords = row["neigh_coords"]
                # neigh_voxel_coords = grid.get_voxel_coords_from_cart(neigh_cart_coords)
                # Get the site symbols.
                # needed to update the dataframe
                site_index = row["site_index"]
                neigh_index = row["neigh_index"]
                dist = row["dist"]

                # get fraction along line where the min is located
                frac = self.get_site_neighbor_frac(
                    site_cart_coords,
                    neigh_cart_coords,
                    site_index,
                    neigh_index,
                )
                radius = frac * dist
                reverse_frac = 1 - frac
                reverse_radius = reverse_frac * dist

                # Get the unique indices to search the dataframe with
                equiv_site_index = row["equiv_site_index"]
                equiv_neigh_index = row["equiv_neigh_index"]

                # create search to find rows with same symbol set and reverse symbol set.
                reverse_condition = (
                    (possible_unique_pairs["equiv_site_index"] == equiv_neigh_index)
                    & (possible_unique_pairs["equiv_neigh_index"] == equiv_site_index)
                    & (possible_unique_pairs["dist"] == dist)
                )
                # assign the fraction along the line and distance to each unique
                # site neighbor pair. We do this in the loop so that the reverse
                # assignments don't need to be repeated
                possible_unique_pairs.at[index, "partitioning_frac"] = frac
                possible_unique_pairs.loc[reverse_condition, "partitioning_frac"] = (
                    reverse_frac
                )

                # create another search condition for the full dataframe of site-neighbor pairs
                search_condition1 = (
                    (possible_site_neigh_pairs["equiv_site_index"] == equiv_site_index)
                    & (
                        possible_site_neigh_pairs["equiv_neigh_index"]
                        == equiv_neigh_index
                    )
                    & (possible_site_neigh_pairs["dist"] == dist)
                )
                reverse_condition1 = (
                    (possible_site_neigh_pairs["equiv_site_index"] == equiv_neigh_index)
                    & (
                        possible_site_neigh_pairs["equiv_neigh_index"]
                        == equiv_site_index
                    )
                    & (possible_site_neigh_pairs["dist"] == dist)
                )

                # Assign the fraction along the line and distance to every
                # site neighbor pair.
                possible_site_neigh_pairs.loc[
                    search_condition1, ["partitioning_frac", "radius"]
                ] = (frac, radius)
                possible_site_neigh_pairs.loc[
                    reverse_condition1, ["partitioning_frac", "radius"]
                ] = (reverse_frac, reverse_radius)
        # Get the site and neighbor coords in arrays to make calculations easier
        site_coords = np.array(possible_site_neigh_pairs["site_coords"].to_list())
        neigh_coords = np.array(possible_site_neigh_pairs["neigh_coords"].to_list())
        fracs = possible_site_neigh_pairs["partitioning_frac"].to_numpy()

        # Calculate the plane points and vectors
        vectors = neigh_coords - site_coords
        magnitudes = np.linalg.norm(vectors, axis=1)
        unit_vectors = vectors / magnitudes[:, np.newaxis]
        plane_points = vectors * fracs[:, np.newaxis] + site_coords

        # Add plane points and vectors to full dataframe
        possible_site_neigh_pairs["plane_points"] = list(plane_points)
        possible_site_neigh_pairs["plane_vectors"] = list(unit_vectors)
        return possible_site_neigh_pairs

    def reduce_to_symmetric_partitioning(self, initial_partitioning: dict):
        """
        Reduces a set of partitioning planes by checking that each plane has
        an equivalent counterpart for the neighboring atom and removing it
        if not.

        Args:
            initial_partitioning (dict):
                A dictionary with site indices as keys and partitioning dataframes
                as values

        Returns:
            A new dictionary of partitioning dataframes for each site.
        """
        equivalent_atoms = self.grid.equivalent_atoms
        unique_atoms = list(set(equivalent_atoms))

        planes_to_keep = {}

        for atom in unique_atoms:
            partitioning_df = initial_partitioning[atom]
            atom_planes_to_keep = []
            # check each plane in the partitioning df
            for i, row in partitioning_df.iterrows():
                neigh_index = row["neigh_index"]
                # get the partitioning to check against
                equiv_neigh_index = equivalent_atoms[neigh_index]
                # get the distance for this site neighbor pair
                dist = row["dist"]
                neigh_partitioning_df = initial_partitioning[equiv_neigh_index]
                # if the reverse exists in the neighbors partitioning keep this
                # plane.
                if dist in neigh_partitioning_df["dist"].to_list():
                    atom_planes_to_keep.append(i)
            planes_to_keep[atom] = atom_planes_to_keep

        new_partitioning = {}
        for i, partitioning_df in initial_partitioning.items():
            equivalent_atom = equivalent_atoms[i]
            indices = planes_to_keep[equivalent_atom]
            new_partitioning_df = partitioning_df.iloc[indices].copy()
            new_partitioning_df.sort_values(by=["dist"], inplace=True)
            new_partitioning_df.reset_index(inplace=True, drop=True)
            new_partitioning[i] = new_partitioning_df
        return new_partitioning

    def increase_to_symmetric_partitioning(self, initial_partitioning: dict):
        """
        Adds to a set of partitioning planes by checking that each plane has
        an equivalent counterpart for the neighboring atom and adding it
        if not.

        Args:
            initial_partitioning (dict):
                A dictionary with site indices as keys and partitioning dataframes
                as values

        Returns:
            A new dictionary of partitioning dataframes for each site.
        """
        equivalent_atoms = self.grid.equivalent_atoms
        site_indices = [i for i in range(len(self.grid.structure))]
        new_partitioning = {}
        for site in site_indices:
            # Look through each other unique atom.
            part_df = initial_partitioning[site]
            site_coords = part_df.loc[0, "site_coords"]
            for neigh in site_indices:
                if neigh != site:
                    neigh_part_df = initial_partitioning[neigh]
                    # Get the planes connecting this neighbor to the site
                    important_neigh_df = neigh_part_df.loc[
                        neigh_part_df["neigh_index"] == site
                    ]
                    # For each plane we want to do the following:
                    # 1. Check if the original site has this plane
                    # 2. Transform the coords of the neigh
                    # 3. Flip the partitioning frac and radius
                    # 4. transform plane point and flip plane vector
                    for i, row in important_neigh_df.iterrows():
                        dist = row["dist"]
                        condition = (part_df["dist"] == dist) & (
                            part_df["neigh_index"] == neigh
                        )
                        if len(part_df.loc[condition]) == 0:
                            # We want to add a new row
                            transformation_vector = row["neigh_coords"] - site_coords
                            new_row = {
                                "site_index": site,
                                "neigh_index": neigh,
                                "equiv_site_index": equivalent_atoms[site],
                                "equiv_neigh_index": equivalent_atoms[neigh],
                                "site_symbol": row["neigh_symbol"],
                                "neigh_symbol": row["site_symbol"],
                                "dist": dist,
                                "site_coords": site_coords,
                                "neigh_coords": row["site_coords"]
                                + transformation_vector,
                                "partitioning_frac": 1 - row["partitioning_frac"],
                                "radius": dist - row["radius"],
                                "plane_points": row["plane_points"]
                                + transformation_vector,
                                "plane_vectors": row["plane_vectors"] * -1,
                            }
                            part_df.loc[len(part_df)] = new_row
            part_df.sort_values(by=["dist"], inplace=True)
            part_df.reset_index(inplace=True, drop=True)
            new_partitioning[site] = part_df
        return new_partitioning

    def get_partitioning(self):
        """
        Gets the partitioning planes for each atom as well as some other useful
        information.

        Returns:
            A dictionary where the keys are site indices and the values
            are neighbor dictionaries containing information on the partitioning
            planes.
        """
        structure = self.grid.structure
        equivalent_atoms = self.grid.equivalent_atoms
        unique_atoms = list(set(equivalent_atoms))
        possible_site_neigh_pairs = self.maximum_site_neighbor_pairs
        # seperate the possible site neighbor pairs into individual atomic sites
        site_dataframes = []
        for site_index, site in enumerate(structure):
            site_dataframe = possible_site_neigh_pairs.loc[
                possible_site_neigh_pairs["site_index"] == site_index
            ].copy()
            site_dataframe.sort_values(by="dist", inplace=True)
            site_dataframes.append(site_dataframe)

        # Now we want to reduce the planes more rigorously by finding where each
        # set of three planes intersect and determining if these points are
        # important to the partitioning surface. We only do this for each unique
        # atom and then we'll fill in the other atoms afterwards
        logging.info("Reducing to necessary partitioning planes")
        important_plane_indices = {}
        for site_index in tqdm(unique_atoms, total=len(unique_atoms), ascii="░▒▓"):
            # get the plane dataframe for this site
            site_dataframe = site_dataframes[site_index]
            # get the plane points and vectors for this site
            plane_points = site_dataframe["plane_points"].to_list()
            plane_vectors = site_dataframe["plane_vectors"].to_list()
            planes = np.concatenate(
                (np.array(plane_points), np.array(plane_vectors)), axis=1
            )
            planes[np.where(planes == 0)] = 1e-12
            dists = site_dataframe["dist"]
            site_cart_coord = structure[site_index].coords
            # reduce the planes by checking if any of the line segments
            # between the planes and sites are intersected by more than 2 planes
            # other than the corresponding plane
            _, reduced_plane_points, reduced_plane_vectors = self._reduce_planes_quick(
                plane_points, plane_vectors, dists, site_cart_coord
            )
            reduced_planes = np.concatenate(
                (reduced_plane_points, reduced_plane_vectors), axis=1
            )
            reduced_planes[np.where(reduced_planes == 0)] = 1e-12
            important_planes = reduced_planes.copy()
            # Get the important planes more rigorously by checking which planes
            # contribute to the vertices of the polyhedral shape surrounding
            # the site
            # _, reduced_planes = self.get_important_planes(reduced_planes)
            # reduced_planes = np.array(reduced_planes)
            # get the indices for the important planes and append them to our
            # dictionary
            indices = np.where((planes[:, None] == important_planes).all(axis=2))[1]
            important_plane_indices[site_index] = indices

        # Go through each site, get the corresponding important planes using
        # the indices we just found, and add to a partitioning dataframe
        initial_partitioning = {}
        for site_index, site_dataframe in enumerate(site_dataframes):
            equiv_atom = equivalent_atoms[site_index]
            important_plane_index = important_plane_indices[equiv_atom]
            site_dataframe = site_dataframe.iloc[important_plane_index].copy()
            site_dataframe.sort_values(by=["dist"], inplace=True)
            site_dataframe.reset_index(inplace=True, drop=True)
            initial_partitioning[site_index] = site_dataframe

        # partitioning = self.reduce_to_symmetric_partitioning(
        #     initial_partitioning
        # )
        # partitioning = self.increase_to_symmetric_partitioning(initial_partitioning)
        # return partitioning
        return initial_partitioning

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
            partition_results, _ = self.get_partitioning()

        # Create a matplotlib plot
        import matplotlib
        import matplotlib.pyplot as plt

        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")

        # Get the vertices of the polygons formed by the partitioning around
        # each atom
        atoms_polygon_nodes = {}
        for site_index, neighbor_df in partition_results.items():
            planes = []
            for neigh_index, row in neighbor_df.iterrows():
                plane_point = list(row["plane_points"])
                plane_vector = list(row["plane_vectors"])
                plane = plane_vector + plane_point
                planes.append(plane)
            intercepts, _ = self.get_important_planes(planes)
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
