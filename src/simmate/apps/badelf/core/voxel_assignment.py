# -*- coding: utf-8 -*-

import itertools
import logging
import math
from functools import cached_property
from pathlib import Path

import dask.array as da
import numpy as np
import psutil
from numpy.typing import ArrayLike
from tqdm import tqdm

from simmate.apps.badelf.core.grid import Grid
from simmate.toolkit import Structure


class VoxelAssignmentToolkit:
    """
    A set of tools for assigning charge to atoms in a unit cell.

    Args:
        charge_grid (Grid):
            A BadELF app Grid type object usually with CHGCAR type data.
        partitioning_grid (Grid):
            A BadELF app Grid type object usually with ELFCAR type data.
        algorithm (str):
            The algorithm to use for partitioning. Defaults to BadELF
        partitioning (dict):
            A partitioning dictionary generated from the BadELF app
            PartitioningToolkit. Will be generated from the grid if None.
        electride_structure (Structure):
            The structure with electride sites. Will be generated if not given.

    """

    def __init__(
        self,
        charge_grid: Grid,
        electride_structure: Structure,
        algorithm: str,
        partitioning: dict,
        directory: Path,
    ):
        self.charge_grid = charge_grid.copy()
        self.algorithm = algorithm
        # partitioning will contain electride sites for voronelf
        self.partitioning = partitioning
        self.electride_structure = electride_structure

    @property
    def unit_cell_permutations_vox(self):
        """
        The permutations required to transform a unit cell to each of its neighbors.
        Uses voxel coordinates.
        """
        return self.charge_grid.permutations

    @property
    def unit_cell_permutations_frac(self):
        """
        The permutations required to transform a unit cell to each of its neighbors.
        Uses fractional coordinates.
        """
        unit_cell_permutations_frac = [
            (t, u, v)
            for t, u, v in itertools.product([-1, 0, 1], [-1, 0, 1], [-1, 0, 1])
        ]
        # move 0,0,0 transformation to front as it is the most likely to be important
        unit_cell_permutations_frac.insert(0, unit_cell_permutations_frac.pop(13))
        return unit_cell_permutations_frac

    @property
    def unit_cell_permutations_cart(self):
        """
        The permutations required to transform a unit cell to each of its neighbors.
        Uses cartesian coordinates.
        """
        grid = self.charge_grid
        return grid.get_cart_coords_from_frac_full_array(
            self.unit_cell_permutations_frac
        )

    @property
    def vertices_transforms_frac(self):
        """
        The transformations required to transform the center of a voxel to its
        corners. Uses fractional coordinates.
        """
        a, b, c = self.charge_grid.grid_shape
        a1, b1, c1 = 1 / (2 * a), 1 / (2 * b), 1 / (2 * c)
        x, y, z = np.meshgrid([-a1, a1], [-b1, b1], [-c1, c1])
        vertices_transforms_frac = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
        return vertices_transforms_frac

    @property
    def vertices_transforms_cart(self):
        """
        The transformations required to transform the center of a voxel to its
        corners. Uses cartesian coordinates.
        """
        return self.charge_grid.get_cart_coords_from_frac_full_array(
            self.vertices_transforms_frac
        )

    @cached_property
    def all_voxel_frac_coords(self):
        """
        The fractional coordinates for all of the voxels in the charge grid
        """
        return self.charge_grid.all_voxel_frac_coords

    @cached_property
    def all_partitioning_plane_points_and_vectors(self):
        """
        The points and vectors for all of the partitioning planes stored as
        two sets of N,3 shaped arrays.
        """
        partitioning = self.partitioning
        plane_points = []
        plane_vectors = []
        for atom_index, partitioning_df in partitioning.items():
            atom_plane_points = partitioning_df["plane_points"].to_list()
            atom_plane_vectors = partitioning_df["plane_vectors"].to_list()
            plane_points.extend(atom_plane_points)
            plane_vectors.extend(atom_plane_vectors)

        # convert plane points and vectors to arrays and then convert to the plane
        # equation
        plane_points = np.array(plane_points)
        plane_vectors = np.array(plane_vectors)
        return plane_points, plane_vectors

    @cached_property
    def all_plane_equations(self):
        """
        A (N,4) array containing every partitioning plane equation
        """
        plane_points, plane_vectors = self.all_partitioning_plane_points_and_vectors
        D = -np.sum(plane_points * plane_vectors, axis=1)
        # convert to all coefficients
        return np.column_stack((plane_vectors, D))

    @cached_property
    def number_of_planes_per_atom(self):
        """
        A list for splitting an array containing all of the partitioning planes
        back into atom based sections.
        """
        partitioning = self.partitioning
        number_of_planes_per_atom = [len(planes) for planes in partitioning.values()]
        number_of_planes_per_atom.pop(-1)
        number_of_planes_per_atom = np.array(number_of_planes_per_atom)
        sum_number_of_planes_per_atom = []
        for i, j in enumerate(number_of_planes_per_atom):
            sum_number_of_planes_per_atom.append(
                j + np.sum(number_of_planes_per_atom[:i])
            )
        return sum_number_of_planes_per_atom

    @cached_property
    def voxel_edge_vectors(self):
        """
        A (12,3) array consisting of the vectors that make up the edges of
        a voxel in the grid
        """
        # Here we define the edges of each voxel in terms of vertex indices. these are
        # not unique and other choices could be made. One potentially faster option is
        # to arrange the edges so that the first index is as small of a set of indices
        # as possible. Later when we calculate t in our line segments this would reduce
        # the number of calculations needed for the numerator which only depends on
        # the plane equation and the first vertex position
        # Get the edge vectors in cartesian coordinates
        vertices_transforms_cart = self.vertices_transforms_cart
        edges = np.array(
            [
                [0, 1],
                [0, 2],
                [0, 4],
                [3, 1],
                [3, 2],
                [3, 7],
                [5, 1],
                [5, 4],
                [5, 7],
                [6, 2],
                [6, 4],
                [6, 7],
            ]
        )
        edge_vectors = []
        for edge in edges:
            edge_vector = (
                vertices_transforms_cart[edge[1]] - vertices_transforms_cart[edge[0]]
            )
            edge_vectors.append(edge_vector)
        edge_vectors = np.array(edge_vectors)
        return edge_vectors

    def get_site_assignments_from_frac_coords(
        self,
        voxel_frac_coords: ArrayLike,
        min_dist_from_plane: float,
    ):
        """
        Gets the site assignments for an arbitrary number of voxels described
        by their fractional coordinates.

        Args:
            voxel_frac_coords (ArrayLike):
                An N,3 array of fractional coordinates corresponding to the voxels
                to assign sites to
            min_dist_from_plane (float):
                The minimum distance a point should be from the plane before
                a site can be assigned. This is value usually corresponds to
                the maximum distance the voxel center can be from the plane
                while the voxel is still being intersected by the plane.

        Returns:
            A 1D array of atomic site assignments. Assignments start at 1 with
            0 indicating no site was found for this coordinate.
        """
        grid = self.charge_grid
        plane_equations = self.all_plane_equations
        number_of_planes_per_atom = self.number_of_planes_per_atom
        unit_cell_permutations_frac = self.unit_cell_permutations_frac

        # Create an array of zeros to map back to
        zeros_array = np.zeros(len(voxel_frac_coords))
        # Create an array that the results will be added to
        results_array = zeros_array.copy()

        # create zeros array for any problems
        # global_indices_to_zero = np.array([])
        # check every possible permutation
        for transformation in tqdm(
            unit_cell_permutations_frac,
            total=len(unit_cell_permutations_frac),
            ascii="░▒▓",
        ):
            # Get the indices where voxels haven't been assigned. Get only these
            # frac coords
            indices_where_zero = np.where(results_array == 0)[0]
            new_frac_coords = voxel_frac_coords.copy()[indices_where_zero]
            # transform the fractional coords to the next transformation
            x1, y1, z1 = transformation
            new_frac_coords[:, 0] += x1
            new_frac_coords[:, 1] += y1
            new_frac_coords[:, 2] += z1
            # Convert the frac coords into cartesian coords
            cart_coords = grid.get_cart_coords_from_frac_full_array(
                new_frac_coords
            ).astype(float)
            points = np.array(cart_coords).astype(float)
            planes = np.array(plane_equations).astype(float)
            # There is a difference in the speed of dask vs numpy. Dask has a
            # lot of overhead, but at a certain point it is faster than numpy.
            # We check which one we should use here.
            plane_distances_to_calc = len(points) * len(planes)
            if plane_distances_to_calc > 7.8e8:
                dask = True
            else:
                dask = False

            if dask:
                # DASK ARRAY VERSION
                # points = da.from_array(points)
                # planes = da.from_array(planes)
                distances = da.dot(points, planes[:, :3].T) + planes[:, 3]
                # Round the distances to within 5 decimals. Everything to this point has
                # been based on lattice position from vasp which typically have 5-6
                # decimal places (7 sig figs)
                distances = np.round(distances, 12)
                # We write over the distances with a more simplified boolean to save
                # space. This is also where we filter if we're near a plane if desired
                distances = da.where(distances < -min_dist_from_plane, True, False)
                distances = distances.compute()

            else:
                # BASE NUMPY VERSION
                distances = np.dot(points, planes[:, :3].T) + planes[:, 3]
                # Round the distances to within 5 decimals. Everything to this point has
                # been based on lattice position from vasp which typically have 5-6
                # decimal places (7 sig figs)
                distances = np.round(distances, 12)
                # We write over the distances with a more simplified boolean to save
                # space. This is also where we filter if we're near a plane if desired
                distances = np.where(distances < -min_dist_from_plane, True, False)

            # split the array into the planes belonging to each atom. Again we write
            # over to save space
            distances = np.array_split(distances, number_of_planes_per_atom, axis=1)
            # get a 1D array representing the voxel indices with the atom index where the
            # voxel is assigned to a site and 0s where they are not
            new_results_arrays = []
            # for atom_index, atom_array in enumerate(distances_split_by_atom):
            for atom_index, atom_array in enumerate(distances):
                voxel_result = np.all(atom_array, axis=1)
                voxel_result = np.where(
                    voxel_result == True, atom_index + 1, voxel_result
                )
                new_results_arrays.append(voxel_result)

            indices_to_zero = []
            new_results_array = np.zeros(len(new_results_arrays[0]))
            for i, sub_results_array in enumerate(new_results_arrays):
                new_results_array = np.sum(
                    [new_results_array, sub_results_array], axis=0
                )
                indices_to_zero.extend(np.where(new_results_array > i + 1)[0])
            indices_to_zero = np.unique(indices_to_zero).astype(int)
            # print(len(indices_to_zero))
            new_results_array[indices_to_zero] = 0
            # Sum the results
            # new_results_array = np.sum(new_results_arrays, axis=0)
            # add results to the results_array
            results_array[indices_where_zero] = new_results_array
        return results_array

    def get_site_assignments_from_frac_coords_with_memory_handling(
        self,
        voxel_frac_coords: ArrayLike,
        min_dist_from_plane: float,
    ):
        """
        Gets the site assignments for an arbitrary number of voxels described
        by their fractional coordinates. Takes available memory into account
        and divides the voxels into chunks to perform operations.

        Args:
            voxel_frac_coords (ArrayLike):
                An N,3 array of fractional coordinates corresponding to the voxels
                to assign sites to
            min_dist_from_plane (float):
                The minimum distance a point should be from the plane before
                a site can be assigned. This is value usually corresponds to
                the maximum distance the voxel center can be from the plane
                while the voxel is still being intersected by the plane.

        Returns:
            A 1D array of atomic site assignments. Assignments start at 1 with
            0 indicating no site was found for this coordinate.
        """
        partitioning = self.partitioning
        # determine how much memory is available. Then calculate how many distance
        # calculations would be possible to do at once with this much memory.
        available_memory = psutil.virtual_memory().available / (1024**2)

        handleable_plane_distance_calcs_numpy = available_memory / 0.00007
        handleable_plane_distance_calcs_dask = available_memory / 0.000025
        plane_distances_to_calc = len(voxel_frac_coords) * sum(
            [len(i) for i in partitioning.values()]
        )

        # I found there is a cutoff where Dask becomes faster than numpy. This
        # may vary with the number of cores available. It is largely due to Dask
        # having a large overhead.
        if plane_distances_to_calc > 7.8e8:
            # calculate the number of chunks the voxel array should be split into to not
            # overload the memory. Then split the array by this number
            split_num = math.ceil(
                plane_distances_to_calc / handleable_plane_distance_calcs_dask
            )
        else:
            split_num = math.ceil(
                plane_distances_to_calc / handleable_plane_distance_calcs_numpy
            )
        split_voxel_frac_coords = np.array_split(voxel_frac_coords, split_num, axis=0)
        # create an array to store results
        voxel_results_array = np.array([])
        # for each split, calculate the results and add to the end of our results
        for chunk, split_voxel_array in enumerate(split_voxel_frac_coords):
            logging.info(
                f"Calculating site assignments for voxel chunk {chunk+1}/{split_num}"
            )
            split_result = self.get_site_assignments_from_frac_coords(
                voxel_frac_coords=split_voxel_array,
                min_dist_from_plane=min_dist_from_plane,
            )
            voxel_results_array = np.concatenate([voxel_results_array, split_result])
        return voxel_results_array

    def get_single_site_voxel_assignments(self, all_site_voxel_assignments: ArrayLike):
        """
        Gets the voxel assignments for voxels that are not split by a plane.

        Args:
            all_site_voxel_assignments (ArrayLike):
                A 1D array of integers representing the site assignments for
                each voxel in the grid.

        Returns:
            A 1D array of the same length as the input with additional site
            assignments.
        """
        all_voxel_assignments = all_site_voxel_assignments.copy()
        # charge_grid = self.charge_grid
        # In the BadELF algorithm the electride sites will have already been
        # assigned. In VoronELF they won't be. Here we search for unassigned
        # voxels and then run the alg on the remaining ones
        unassigned_indices = np.where(all_voxel_assignments == 0)[0]
        all_voxel_frac_coords = self.all_voxel_frac_coords
        frac_coords_to_find = all_voxel_frac_coords[unassigned_indices]
        # min_dist_from_plane = charge_grid.max_voxel_dist
        single_site_voxel_assignments = (
            self.get_site_assignments_from_frac_coords_with_memory_handling(
                frac_coords_to_find, min_dist_from_plane=0
            )
        )
        all_voxel_assignments[unassigned_indices] = single_site_voxel_assignments
        return all_voxel_assignments

    def get_plane_split_voxel_assignments(self, voxel_frac_coords):
        """
        Gets the voxel assignments for voxels that are exactly on a plane.

        Args:
            voxel_frac_coords (ArrayLike):
                A 2D array representing the fractional coordinates of voxels
                that haven't been assigned

        Returns:
            A 2D array of shape (N,M) where N is the length of the input array
            and M is the number of atoms. A 1 means the atom is assigned this
            voxel.
        """
        logging.info("Calculating assignments for voxels on planes")
        if self.algorithm == "badelf":
            structure = self.charge_grid.structure
        elif self.algorithm == "voronelf":
            structure = self.electride_structure
        grid = self.charge_grid
        plane_equations = self.all_plane_equations
        number_of_planes_per_atom = self.number_of_planes_per_atom
        unit_cell_permutations_frac = self.unit_cell_permutations_frac

        # Create an array of zeros to map back to
        zeros_array = np.zeros([len(voxel_frac_coords), len(structure)])
        # Create an array that the results will be added to
        results_array = zeros_array.copy()

        # create zeros array for any problems
        # global_indices_to_zero = np.array([])
        # check every possible permutation
        for transformation in tqdm(
            unit_cell_permutations_frac,
            total=len(unit_cell_permutations_frac),
            ascii="░▒▓",
        ):
            # Get the indices where voxels haven't been assigned. Get only these
            # frac coords
            new_frac_coords = voxel_frac_coords.copy()
            # transform the fractional coords to the next transformation
            x1, y1, z1 = transformation
            new_frac_coords[:, 0] += x1
            new_frac_coords[:, 1] += y1
            new_frac_coords[:, 2] += z1
            # Convert the frac coords into cartesian coords
            cart_coords = grid.get_cart_coords_from_frac_full_array(
                new_frac_coords
            ).astype(float)
            points = np.array(cart_coords).astype(float)
            planes = np.array(plane_equations).astype(float)
            # There is a difference in the speed of dask vs numpy. Dask has a
            # lot of overhead, but at a certain point it is faster than numpy.
            # We check which one we should use here.
            plane_distances_to_calc = len(points) * len(planes)
            if plane_distances_to_calc > 7.8e8:
                dask = True
            else:
                dask = False

            if dask:
                # DASK ARRAY VERSION
                # points = da.from_array(points)
                # planes = da.from_array(planes)
                distances = da.dot(points, planes[:, :3].T) + planes[:, 3]
                # Round the distances to within 5 decimals. Everything to this point has
                # been based on lattice position from vasp which typically have 5-6
                # decimal places (7 sig figs)
                distances = np.round(distances, 12)
                # We write over the distances with a more simplified boolean to save
                # space. This is also where we filter if we're near a plane if desired
                distances = da.where(distances <= 0, True, False)
                distances = distances.compute()

            else:
                # BASE NUMPY VERSION
                distances = np.dot(points, planes[:, :3].T) + planes[:, 3]
                # Round the distances to within 5 decimals. Everything to this point has
                # been based on lattice position from vasp which typically have 5-6
                # decimal places (7 sig figs)
                distances = np.round(distances, 12)
                # We write over the distances with a more simplified boolean to save
                # space. This is also where we filter if we're near a plane if desired
                distances = np.where(distances <= 0, True, False)

            # split the array into the planes belonging to each atom. Again we write
            # over to save space
            distances = np.array_split(distances, number_of_planes_per_atom, axis=1)
            # get a 1D array representing the voxel indices with the atom index where the
            # voxel is assigned to a site and 0s where they are not
            new_results_arrays = []
            # for atom_index, atom_array in enumerate(distances_split_by_atom):
            for atom_index, atom_array in enumerate(distances):
                voxel_result = np.all(atom_array, axis=1)
                voxel_result = np.where(
                    voxel_result == True, atom_index + 1, voxel_result
                )
                new_results_arrays.append(voxel_result)

            # add results to the results_array
            results_array += np.column_stack(new_results_arrays)

        results_array = np.where(results_array > 0, 1, 0)
        return results_array

    def get_multi_site_voxel_assignments(self, all_site_voxel_assignments):
        """
        Gets the voxel assignments for voxels that are not split by a plane.

        Args:
            all_site_voxel_assignments (ArrayLike):
                A 1D array of integers representing the site assignments for
                each voxel in the grid.

        Returns:
            A 2D array of fractional site assignments with indices (i,j) where i is the
            voxel index and j is the site index.
        """
        grid = self.charge_grid
        # Get all site assignments so far
        all_site_voxel_assignments = all_site_voxel_assignments.copy()
        # Check that there are any unassigned voxels. If none, return an empty
        # array
        if len(np.where(all_site_voxel_assignments == 0)[0]) == 0:
            return np.array([])
        # The following lines are a more rigorous method of calculating the voxels
        # directly on planes. It takes longer so it's commented for now.
        # Now we want to get assignments for voxels directly on planes
        # all_frac_coords = grid.all_voxel_frac_coords
        # unassigned_indices_1d = np.where(all_site_voxel_assignments==0)[0]
        # unassigned_frac_coords = all_frac_coords[unassigned_indices_1d]
        # on_plane_assignment = self.get_plane_split_voxel_assignments(unassigned_frac_coords)
        # Some of the voxels will have been assigned. We want to store the indices of
        # these so we can zero them out later

        # Get as unassigned grid
        assignment_array = all_site_voxel_assignments.reshape(grid.shape).astype(
            np.int16
        )
        unassigned_indices = np.column_stack(np.where(assignment_array == 0))
        # If doing self we don't want assignments to go to electrides so we zero them
        # here. We need to save them to put them back later though
        if self.algorithm == "badelf":
            electride_indices = (
                np.array(self.electride_structure.indices_from_symbol("He")) + 1
            )
            assignment_array = np.where(
                np.isin(assignment_array, electride_indices), 0, assignment_array
            )
            structure = grid.structure
        elif self.algorithm == "voronelf":
            structure = self.electride_structure
        # Get smallest radius for a sphere
        lattice = grid.structure.lattice

        # Get the starting radius/min_radius and the maximum radius we could possibly
        # go to
        nearest_voxels = lattice.abc / grid.shape
        min_radius = nearest_voxels.max()
        test_radius = min_radius.copy()
        max_radius = (np.array(lattice.abc) / 2).max()

        # Get array to assign to
        # new_assignment_array = on_plane_assignment.copy()
        new_assignment_array = np.zeros([len(unassigned_indices), len(structure)])

        while len(np.where(np.sum(new_assignment_array, axis=1) == 0)[0]) > 0:
            if test_radius >= max_radius:
                raise Exception()
            # Get the transformations to get a sphere around a voxel
            sphere_transforms = grid.get_voxels_transformations_to_radius(test_radius)
            # Get the indices that still don't have an assignment
            still_unassigned_1d_indices = np.where(
                np.sum(new_assignment_array, axis=1) == 0
            )[0]
            # Get the voxel coords of the unassigned indices
            unassigned_voxel_coords = unassigned_indices[still_unassigned_1d_indices]
            possible_assignments = []
            # for each voxel in the sphere around the voxel, get the site assignment
            for transform in sphere_transforms:
                new_indices = unassigned_voxel_coords + transform
                # wrap around indices
                new_x = (new_indices[:, 0] % grid.shape[0]).astype(int)
                new_y = (new_indices[:, 1] % grid.shape[1]).astype(int)
                new_z = (new_indices[:, 2] % grid.shape[2]).astype(int)
                site_assignment = assignment_array[new_x, new_y, new_z]
                possible_assignments.append(site_assignment)
            possible_assignments = np.column_stack(possible_assignments)
            # Get the assignments that are not still 0
            non_zero_indices = np.where(np.sum(possible_assignments, axis=1) > 0)[0]
            sub_possible_assignments = possible_assignments[non_zero_indices]
            # iterate over these assignments and count how many there are of each.
            # Update the corresponding row in the new assignments array with total
            # count for each site.
            for i, possible_label in enumerate(sub_possible_assignments):
                sites, counts = np.unique(possible_label, return_counts=True)
                for site, count in zip(sites[1:], counts[1:]):
                    new_assignment_array[
                        still_unassigned_1d_indices[non_zero_indices[i]], site - 1
                    ] = count
            # increase our test radius for the next round
            test_radius += min_radius
            # print(test_radius, len(np.where(np.sum(new_assignment_array,axis=1)==0)[0]))

        # We need to rescale the assignment array to check for any that have assignments
        # much higher than 0.5
        new_assignment_array_sum = np.tile(
            np.sum(new_assignment_array, axis=1), (len(new_assignment_array[0]), 1)
        ).T
        new_assignment_array = new_assignment_array / new_assignment_array_sum
        return new_assignment_array
