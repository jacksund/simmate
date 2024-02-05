# -*- coding: utf-8 -*-

import logging
import math
from functools import cached_property
from itertools import combinations

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
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
        grid (Grid): A BadELF app Grid type object.
    """

    def __init__(self, grid: Grid):
        self.grid = grid.copy()

    def get_partitioning_line_from_voxels(
        self,
        site_voxel_coord: ArrayLike | list,
        neigh_voxel_coord: ArrayLike | list,
        # method: str = "linear",
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
        # values = savgol_filter(values, 20, 3)
        return line, values

    def get_partitioning_line_from_indices(self, i: int, j: int):
        """
        Gets the voxel positions and elf values for points between two sites in
        the structure.

        Parameters:
        - i: index of first site in the structure
        - j: index of second site in the structure

        Returns:
        - Two lists, one of positions in voxel coordinates and another of elf
        values
        """
        grid = self.grid.copy()
        site_voxel_coord = grid.get_voxel_coords_from_index(i)
        neigh_voxel_coord = grid.get_voxel_coords_from_index(j)
        return self.get_partitioning_line_from_voxels(
            site_voxel_coord, neigh_voxel_coord
        )

    def get_partitioning_line_from_cart_coords(
        self, site_cart_coords, neigh_cart_coords
    ):
        """
        Gets the voxel positions and elf values for points between two sites in
        the structure given as cartesian coordinates. This method can also be
        used to find the values in the ELF between two arbitrary points in the
        structure.

        Parameters:
        - site_cart_coords: cartesian coordinates of a site in the structure
        - neigh_cart_coords: cartesian coordinates of a second site in the structure

        Returns:
        - Two lists, one of positions in voxel coordinates and another of elf
        values
        """
        grid = self.grid.copy()
        site_voxel_coord = grid.get_voxel_coords_from_cart(site_cart_coords)
        neigh_voxel_coord = grid.get_voxel_coords_from_cart(neigh_cart_coords)
        return self.get_partitioning_line_from_voxels(
            site_voxel_coord, neigh_voxel_coord
        )

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

    def get_line_minimum_as_frac(
        self,
        positions: list,
        values: list | ArrayLike,
        site_string: str,
        neigh_string: str,
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
            site_string (str):
                The symbol of the atom at the start of the line
            neigh_string (str):
                The symbol of the atom at the end of the line

        results:
            The global minimum of form [line_position, value, frac_position]
        """

        if site_string == neigh_string:
            list_values = list(values)
            # We have the same type of atom on either side. We want to check
            # if they are the same and if they are return a frac of 0.5. This
            # is because usually there will be some slight covalency between
            # atoms of the same type, but they should share the area equally
            symmetric = self._check_partitioning_line_for_symmetry(list_values)
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
            minima = self.find_minimum(values)
            # maxima = find_maximum(values)

            # then we grab the local minima closest to the midpoint of the values
            global_min = self.get_closest_extrema_to_center(values, minima)
            global_min = self._refine_line_min_frac(
                positions=positions, elf_min_index=global_min[0]
            )

        return global_min

    def _refine_line_min_frac(self, positions, elf_min_index):
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

        results:
            The global minimum of form [line_position, value, frac_position]
        """
        amount_to_pad = 10
        grid = self.grid.copy()
        padded = np.pad(grid.total, amount_to_pad, mode="wrap")

        # interpolate the grid with a more rigorous method to find more exact value
        # for the plane.
        a, b, c = grid.get_grid_axes(10)
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
                    new_pos = [i + amount_to_pad - 1 for i in pos]
                    value_fine = float(fn(new_pos))
                    values_fine.append(value_fine)

                # Find the minimum value of this line as well as the index for this value's
                # position.
                minimum_value = min(values_fine)
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
                new_pos = [i + amount_to_pad - 1 for i in pos]
                value = float(fn(new_pos))
                values.append(value)

            # Get a list of all of the minima along the line
            minima = self.find_minimum(values)

            # then we grab the local minima closest to the midpoint of the line
            global_min = self.get_closest_extrema_to_center(values, minima)

            # now we want a small section of the line surrounding the minimum
            values_fine = values[global_min[0] - 3 : global_min[0] + 4]
            line_section_x = [i for i in range(global_min[0] - 3, global_min[0] + 4)]

        # now that we've found the values surrounding the minimum of our line,
        # we can fit these values to a 2nd degree polynomial and solve for its
        # minimum point
        d, e, f = np.polyfit(line_section_x, values_fine, 2)
        x = -e / (2 * d)
        elf_min_index_new = x
        elf_min_value_new = np.polyval(np.array([d, e, f]), x)
        elf_min_frac_new = elf_min_index_new / (len(positions) - 1)

        return [elf_min_index_new, elf_min_value_new, elf_min_frac_new]

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
        # get closest neighbor for the given site
        neighbors = structure.get_neighbors(structure[site_index], 15)

        # Get the closest neighbor to the site. We put the nearest neighbors in
        # a dataframe, sort by distance, and then select the nearest one.
        site_df = pd.DataFrame(columns=["neighbor", "distance"])
        for neigh in neighbors:
            # get distance
            distance = math.dist(neigh.coords, structure[site_index].coords)
            # add neighbor, distance pair to df
            site_df.loc[len(site_df)] = [neigh, distance]
        # sort by distance and truncate to first 50
        site_df = site_df.sort_values(by="distance")
        for i, row in site_df.iterrows():
            neigh = row["neighbor"]
            if neigh.species_string != "He":
                closest_neighbor = neigh
                bond_dist = row["distance"]
                break
            else:
                continue

        # Get site voxel coords from cartesian coordinates
        site_voxel_coord = self.grid.get_voxel_coords_from_cart(
            structure[site_index].coords
        )
        # Get neighbor voxel coords and then the line between the sites/voxels
        neigh_voxel_coord = self.grid.get_voxel_coords_from_cart(
            closest_neighbor.coords
        )
        elf_positions, elf_values = self.get_partitioning_line_from_voxels(
            site_voxel_coord,
            neigh_voxel_coord,
            method,
        )

        # Get site and neighbor strings
        site_string = self.grid.structure[site_index].species_string
        neighbor_string = closest_neighbor.species_string

        max_bond_dist = (
            structure[site_index].specie.atomic_radius
            + closest_neighbor.specie.atomic_radius
        )
        # If the bond is larger than the some of both atomic radii it is likely
        # that there is an electride between the atom and its closest neighbor.
        # We want to get the distance to the minimum closer to the atom than
        # its neighbor.
        if bond_dist > max_bond_dist:
            # We get all of the minima along  the line. We then find the distance
            # of each minima from the middle of the line, remove any that are
            # closer to the neighboring atom, and find the one closest to the
            # center of the bond.
            minima = self.find_minimum(elf_values)
            mid_point = len(elf_values) / 2
            dists_to_min = np.array([mid_point - x[0] for x in minima])
            dists_to_min = dists_to_min[dists_to_min >= 0]
            min_pos = minima[np.argmin(dists_to_min)]
            # Append the fractional distance to the minimum of the line.
            min_pos.append(min_pos[0] / (len(elf_values) - 1))
        else:
            # Get the min position along the line
            min_pos = self.get_line_minimum_as_frac(
                elf_positions, elf_values, site_string, neighbor_string
            )
        #!!! This is the only place some of these methods are used. Is this necessary
        # or could they be removed somehow with the new methods?
        min_voxel_coord = self.get_voxel_coords_from_min_along_line(
            min_pos[2], site_voxel_coord, neigh_voxel_coord
        )
        min_cart_coord = self.grid.get_cart_coords_from_vox(min_voxel_coord)
        distance_to_min = self.get_distance_to_min(min_cart_coord, site_voxel_coord)

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

        Returns three arrays corresponding to the indices of the reduced planes,
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
        structure = self.grid.structure
        logging.info("Getting all neighboring atoms for each site in structure")
        # Get all neighbors within 15 Angstrom
        nearest_neighbors = structure.get_neighbor_list(15)
        # Create dataframe with important info about each site/neighbor pair
        site_neigh_pairs = pd.DataFrame()
        # Add sites and neighbors indices
        site_neigh_pairs["site_index"] = nearest_neighbors[0]
        site_neigh_pairs["neigh_index"] = nearest_neighbors[1]
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
            self.grid.get_cart_coords_from_frac_full_array(neigh_frac_coords)
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

        Returns:
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

        # Get all possible neighbor atoms for each atom within 15 angstroms
        all_neighbors = structure.get_all_neighbors(15)
        neighbors = []

        for site, neighs in enumerate(all_neighbors):
            # Get the coordinates for each site/neighbor pair and convert to numpy array
            site_coords = []
            neigh_coords = []
            site_coord = structure[site].coords
            for neigh in neighs:
                neigh_coord = neigh.coords
                site_coords.append(site_coord)
                neigh_coords.append(neigh_coord)
            site_coords = np.array(site_coords)
            neigh_coords = np.array(neigh_coords)
            # Calculate the distance between the site and each neighbor
            distances = np.linalg.norm(neigh_coords - site_coords, axis=1)

            # Create a dataframe of neighbors and distance
            site_df = pd.DataFrame(columns=["neighbors", "distances"])
            site_df["neighbors"] = neighs
            site_df["distances"] = distances
            # sort by distance and truncate to requested length
            site_df = site_df.sort_values(by="distances")
            site_df = site_df.iloc[0:neighbor_num]
            # Append neighbors to our neighbor list
            neighbors.append(site_df["neighbors"].to_list())

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

        # get a smoothed elf line
        values = savgol_filter(values, 20, 3)

        # get the center of the ELF line
        midpoint = len(values) / 2

        # minima function gives all local minima along the values. maxima does the reverse
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
        closest_neighbors = self.get_closest_neighbors(structure)
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

    def check_structure_for_covalency(self):
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
        closest_neighbors = self.get_closest_neighbors(structure)
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
                values = self.get_partitioning_line_from_voxels(
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

    def get_site_neighbor_frac(
        self,
        site_cart_coords: ArrayLike,
        neigh_cart_coords: ArrayLike,
        site_symbol: str,
        neigh_symbol: str,
    ):
        """
        Function for getting the fraction of a line betwaeen two sites where
        the ELF is at a minimum.

        Args:
            site_cart_coords (Array | list):
                The cartesian coordinates of the first site.
            neigh_cart_coords (Array | list):
                The cartesian coordinates of the neighboring site.

        returns:
            The minimum point in the ELF between the two sites.

        """
        grid = self.grid.copy()

        site_voxel_coord = grid.get_voxel_coords_from_cart(site_cart_coords)
        neigh_voxel_coord = grid.get_voxel_coords_from_cart(neigh_cart_coords)

        # we need a straight line between these two points.  get list of all ELF values
        elf_coordinates, elf_values = self.get_partitioning_line_from_voxels(
            site_voxel_coord, neigh_voxel_coord, method="linear"
        )

        # find the minimum position and value along the elf_line
        # the third element is the fractional position, measured from site_voxel_coord
        elf_min_index, elf_min_value, elf_min_frac = self.get_line_minimum_as_frac(
            elf_coordinates,
            elf_values,
            site_symbol,
            neigh_symbol,
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
            planes (list): The list of planes to check

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
                    point=intercept, plane_vector=plane[3:], plane_point=plane[:3]
                )
                if sign in ["positive", "zero"]:
                    pass
                else:
                    important_intercept = False
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
                site_symbol = row["site_symbol"]
                neigh_symbol = row["neigh_symbol"]
                shortest_dist = row["dist"]
                # get fraction along line where the min is located
                frac = self.get_site_neighbor_frac(
                    site_cart_coords, neigh_cart_coords, site_symbol, neigh_symbol
                )
                # Set frac to 2*frac or 1 whichever is larger
                if 2 * frac >= 1:
                    frac = (2 * frac) + 0.1
                else:
                    frac = 1.1
                # get all of the planes at this distance
                planes_at_dist = site_dataframe.loc[
                    site_dataframe["dist"] == shortest_dist
                ]

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
                site_symbol = row["site_symbol"]
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
            ]
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
            subset=["site_symbol", "neigh_symbol", "dist"]
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

                site_symbol = row["site_symbol"]
                neigh_symbol = row["neigh_symbol"]
                dist = row["dist"]

                # get fraction along line where the min is located
                frac = self.get_site_neighbor_frac(
                    site_cart_coords, neigh_cart_coords, site_symbol, neigh_symbol
                )
                radius = frac * dist
                reverse_frac = 1 - frac
                reverse_radius = reverse_frac * dist

                # create search to find rows with same symbol set and reverse symbol set.
                reverse_condition = (
                    (possible_unique_pairs["site_symbol"] == neigh_symbol)
                    & (possible_unique_pairs["neigh_symbol"] == site_symbol)
                    & (possible_unique_pairs["dist"] == dist)
                )
                # assign the fraction along the line and distance to each unique
                # site neighbor pair. We do this in the loop so that the reverse
                # assignments don't need to be repeated
                possible_unique_pairs.at[index, "partitioning_frac"] = frac
                possible_unique_pairs.loc[
                    reverse_condition, "partitioning_frac"
                ] = reverse_frac

                # create another search condition for the full dataframe of site-neighbor pairs
                search_condition1 = (
                    (possible_site_neigh_pairs["site_symbol"] == site_symbol)
                    & (possible_site_neigh_pairs["neigh_symbol"] == neigh_symbol)
                    & (possible_site_neigh_pairs["dist"] == dist)
                )
                reverse_condition1 = (
                    (possible_site_neigh_pairs["site_symbol"] == neigh_symbol)
                    & (possible_site_neigh_pairs["neigh_symbol"] == site_symbol)
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

    def reduce_to_symmetric_partitioning(self, initial_partitioning):
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
            new_partitioning_df = partitioning_df.iloc[indices]
            new_partitioning_df.sort_values(by=["dist"], inplace=True)
            new_partitioning_df.reset_index(inplace=True, drop=True)
            new_partitioning[i] = new_partitioning_df
        return new_partitioning

    def get_partitioning(self, check_for_covalency: bool = True):
        """
        Gets the partitioning planes for each atom as well as some other useful
        information.

        Args:
            check_for_covalency (bool):
                Whether to check the structure for signs of covalency. This can
                be turned off, but it may give strange results!

        Returns:
            A dictionary where the keys are site indices and the values
            are neighbor dictionaries containing information on the partitioning
            planes.
        """
        if check_for_covalency:
            self.check_structure_for_covalency()
        structure = self.grid.structure
        equivalent_atoms = self.grid.equivalent_atoms
        unique_atoms = list(set(equivalent_atoms))
        possible_site_neigh_pairs = self.maximum_site_neighbor_pairs
        # seperate the possible site neighbor pairs into individual atomic sites
        site_dataframes = []
        for site_index, site in enumerate(structure):
            site_dataframe = possible_site_neigh_pairs.loc[
                possible_site_neigh_pairs["site_index"] == site_index
            ]
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
            important_planes = reduced_planes
            # Get the important planes more rigorously by checking which planes
            # contribute to the vertices of the polyhedral shape surrounding
            # the site
            _, important_planes = self.get_important_planes(reduced_planes)
            important_planes = np.array(important_planes)
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
            site_dataframe = site_dataframe.iloc[important_plane_index]
            site_dataframe.sort_values(by=["dist"], inplace=True)
            site_dataframe.reset_index(inplace=True, drop=True)
            initial_partitioning[site_index] = site_dataframe

        partitioning = self.reduce_to_symmetric_partitioning(initial_partitioning)
        return partitioning

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
