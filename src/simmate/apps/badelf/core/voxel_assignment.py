# -*- coding: utf-8 -*-

import itertools
import logging
import math
from functools import cached_property
from pathlib import Path

import dask.array as da
import numpy as np
import pandas as pd
import psutil
from numpy.typing import ArrayLike
from scipy.spatial import ConvexHull
from tqdm import tqdm

from simmate.apps.badelf.core.grid import Grid
from simmate.apps.badelf.core.partitioning import PartitioningToolkit
from simmate.toolkit import Structure
from simmate.workflows.utilities import get_workflow


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
        # partitioning_grid: Grid,
        algorithm: str,
        electride_structure: Structure,
        partitioning: dict,
        directory: Path,
    ):
        # self.partitioning_grid = partitioning_grid.copy()
        self.charge_grid = charge_grid.copy()
        self.algorithm = algorithm
        # partitioning will contain electride sites for voronelf
        self.partitioning = partitioning
        self.electride_structure = electride_structure

    @property
    def electride_sites(self):
        """
        Function for getting the number of sites that are electrides

        Returns:
            A tuple of the indices corresponding to the electride sites in the
            structure.
        """
        structure = self.electride_structure
        if self.algorithm == "badelf":
            return structure.indices_from_symbol("He")
        elif self.algorithm == "voronelf":
            return []

    @property
    def unit_cell_permutations_vox(self):
        return self.charge_grid.permutations

    @property
    def unit_cell_permutations_frac(self):
        unit_cell_permutations_frac = [
            (t, u, v)
            for t, u, v in itertools.product([-1, 0, 1], [-1, 0, 1], [-1, 0, 1])
        ]
        # move 0,0,0 transformation to front as it is the most likely to be important
        unit_cell_permutations_frac.insert(0, unit_cell_permutations_frac.pop(13))
        return unit_cell_permutations_frac

    @property
    def unit_cell_permutations_cart(self):
        grid = self.charge_grid
        return grid.get_cart_coords_from_frac_full_array(
            self.unit_cell_permutations_frac
        )

    @property
    def all_voxel_frac_coords(self):
        charge_grid = self.charge_grid.copy()
        a, b, c = charge_grid.grid_shape
        voxel_indices = np.indices(charge_grid.grid_shape).reshape(3, -1).T
        frac_coords = voxel_indices.copy().astype(float)
        frac_coords[:, 0] /= a - 1
        frac_coords[:, 1] /= b - 1
        frac_coords[:, 2] /= c - 1
        return frac_coords

    @cached_property
    def all_partitioning_plane_points_and_vectors(self):
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

    def get_distance_from_voxels_to_planes(
        self,
        voxel_frac_coords,
        max_dist,
        dask,
    ):
        grid = self.charge_grid
        plane_equations = self.all_plane_equations
        number_of_planes_per_atom = self.number_of_planes_per_atom
        unit_cell_permutations_frac = self.unit_cell_permutations_frac

        # Create an array of zeros to map back to
        zeros_array = np.zeros(len(voxel_frac_coords))
        # Create an array that the results will be added to
        results_array = zeros_array.copy()

        # check every possible permutation
        for transformation in tqdm(
            unit_cell_permutations_frac, total=len(unit_cell_permutations_frac)
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
            if dask:
                # DASK ARRAY VERSION
                # points = da.from_array(points)
                # planes = da.from_array(planes)
                distances = da.dot(points, planes[:, :3].T) + planes[:, 3]
                # Round the distances to within 5 decimals. Everything to this point has
                # been based on lattice position from vasp which typically have 5-6
                # decimal places (7 sig figs)
                distances = np.round(distances, 6)
                # We write over the distances with a more simplified boolean to save
                # space. This is also where we filter if we're near a plane if desired
                distances = da.where(distances <= -max_dist, True, False)
                distances = distances.compute()

            else:
                # BASE NUMPY VERSION
                distances = np.dot(points, planes[:, :3].T) + planes[:, 3]
                # Round the distances to within 5 decimals. Everything to this point has
                # been based on lattice position from vasp which typically have 5-6
                # decimal places (7 sig figs)
                distances = np.round(distances, 6)
                # We write over the distances with a more simplified boolean to save
                # space. This is also where we filter if we're near a plane if desired
                distances = np.where(distances <= -max_dist, True, False)

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

            # get a new array that contains the assignments for all of the atoms
            new_results_array = np.sum(new_results_arrays, axis=0)

            # add results to the results_array
            results_array[indices_where_zero] = new_results_array
        return results_array

    def get_distance_from_voxels_to_planes_with_memory_handling(
        self,
        voxel_frac_coords,
        max_dist,
    ):
        """
        Calculates the distance from each voxel to every partitioning plane. For
        very large grids and partitioning planes lists, the voxels are calculated
        in chunks relative to the available memory.
        """
        partitioning = self.partitioning
        # determine how much memory is available. Then calculate how many distance
        # calculations would be possible to do at once with this much memory.
        #!!!! Is this necessary when using dask? Also I should add a size check to
        # see at which point dask becomes faster than numpy
        available_memory = psutil.virtual_memory().available / (1024**2)

        handleable_plane_distance_calcs_numpy = available_memory / 0.00007
        handleable_plane_distance_calcs_dask = available_memory / 0.000025
        plane_distances_to_calc = len(voxel_frac_coords) * sum(
            [len(i) for i in partitioning.values()]
        )
        # if plane_distances_to_calc > handleable_plane_distance_calcs_numpy:
        if plane_distances_to_calc > 7.8e8:
            dask = True
            print("using dask")
            # calculate the number of chunks the voxel array should be split into to not
            # overload the memory. Then split the array by this number
            split_num = math.ceil(
                plane_distances_to_calc / handleable_plane_distance_calcs_dask
            )
        else:
            dask = False
            print("using numpy")
            # split_num = 1
            split_num = math.ceil(
                plane_distances_to_calc / handleable_plane_distance_calcs_numpy
            )
        split_voxel_frac_coords = np.array_split(voxel_frac_coords, split_num, axis=0)
        # create an array to store results
        voxel_results_array = np.array([])
        # for each split, calculate the results and add to the end of our results
        for chunk, split_voxel_array in enumerate(split_voxel_frac_coords):
            logging.info(f"Calculating voxel chunk {chunk}/{split_num}")
            split_result = self.get_distance_from_voxels_to_planes(
                voxel_frac_coords=split_voxel_array, max_dist=max_dist, dask=dask
            )
            voxel_results_array = np.concatenate([voxel_results_array, split_result])
        return voxel_results_array

    @staticmethod
    def calculate_t_num(points, plane_points, plane_vectors):
        """
        Generalizes the calculation np.dot(plane_vector, (plane_point - point)) to
        an arbitrary number of planes and points. Returns a 2D array with index (i,j)
        with i as the point index and j as the plane index.
        """
        # Reshape arrays for broadcasting
        points_reshaped = points[:, np.newaxis, :].astype(float)
        plane_points_reshaped = plane_points[np.newaxis, :, :].astype(float)
        plane_vectors_reshaped = plane_vectors[np.newaxis, :, :].astype(float)
        # create dask arrays
        points_reshaped = da.from_array(points_reshaped)
        plane_points_reshaped = da.from_array(plane_points_reshaped)
        plane_vectors_reshaped = da.from_array(plane_vectors_reshaped)
        # Calculate the dot product
        result = da.sum(
            plane_vectors_reshaped * (plane_points_reshaped - points_reshaped), axis=2
        )
        return result.compute()

    def calculate_t_den(self, plane_vectors):
        """
        Each of the voxel edge vectors is identical across voxels. This function takes each
        edge vector and gets the dot product with each plane vector. The results is
        a 2D array with indices (i,j) where i is the edge index and j is the plane
        index
        """
        edge_vectors = self.voxel_edge_vectors

        edge_plane_dot_prods = np.dot(edge_vectors, plane_vectors.T)

        # Replace 0s with very small value to avoid errors with dividing by 0
        edge_plane_dot_prods = np.where(
            edge_plane_dot_prods == 0, 1e-18, edge_plane_dot_prods
        )
        return edge_plane_dot_prods

    def get_single_site_voxel_assignments(self, all_site_voxel_assignments):
        """
        Gets the voxel assignments for voxels that are not split by a plane
        """
        all_voxel_assignments = all_site_voxel_assignments.copy()
        charge_grid = self.charge_grid
        # In the BadELF algorithm the electride sites will have already been
        # assigned. In VoronELF they won't be. Here we search for unassigned
        # voxels and then run the alg on the remaining ones
        unassigned_indices = np.where(all_voxel_assignments == 0)[0]
        all_voxel_frac_coords = self.all_voxel_frac_coords
        frac_coords_to_find = all_voxel_frac_coords[unassigned_indices]
        max_dist = charge_grid.max_voxel_dist
        single_site_voxel_assignments = (
            self.get_distance_from_voxels_to_planes_with_memory_handling(
                frac_coords_to_find, max_dist
            )
        )
        all_voxel_assignments[unassigned_indices] = single_site_voxel_assignments
        return all_voxel_assignments

    @property
    def vertices_transforms_frac(self):
        a, b, c = self.charge_grid.grid_shape
        a1, b1, c1 = 1 / (2 * (a)), 1 / (2 * (b)), 1 / (2 * (c))
        x, y, z = np.meshgrid([-a1, a1], [-b1, b1], [-c1, c1])
        vertices_transforms_frac = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
        return vertices_transforms_frac

    @property
    def vertices_transforms_cart(self):
        return self.charge_grid.get_cart_coords_from_frac_full_array(
            self.vertices_transforms_frac
        )

    def get_voxel_vertices_frac_coords_stack(self, voxel_indices):
        """
        The fractional coordinates for the vertices of a given array of voxel
        coordinates. The coordinates are stacked in order of the transformations
        applied to get from the voxel center to the vertices
        """
        all_voxel_frac_coords = self.all_voxel_frac_coords
        multi_site_voxel_indices = voxel_indices
        voxels_split_by_plane_frac_coords = all_voxel_frac_coords[
            multi_site_voxel_indices
        ]
        vertices_transforms_frac = self.vertices_transforms_frac
        # Get vertices frac coords
        voxel_vertices_frac_coords = []
        for vertex_transform in vertices_transforms_frac:
            vertex_frac_coords = voxels_split_by_plane_frac_coords + vertex_transform
            voxel_vertices_frac_coords.append(vertex_frac_coords)
        # Combine into one array for faster assignment
        voxel_vertices_frac_coords_stack = np.concatenate(voxel_vertices_frac_coords)
        return voxel_vertices_frac_coords_stack

    def get_vertices_site_assignments(self, voxel_vertices_frac_coords):
        # Get transformations that will get the vertices of each voxel frac. The amount
        # to shift is 1/2 of a voxel in each direction
        voxel_vertices_frac_coords = voxel_vertices_frac_coords.copy()
        # Get the site assignments for each vertex
        vertices_sites_results_array = (
            self.get_distance_from_voxels_to_planes_with_memory_handling(
                voxel_frac_coords=voxel_vertices_frac_coords, max_dist=0
            )
        )
        # split back into the 8 vertices
        vertices_sites_results_array = np.array_split(vertices_sites_results_array, 8)
        # create an array of site results for each vertex. The rows are voxel indices
        # and the columns are vertex indices
        vertices_sites_results_array = np.vstack(vertices_sites_results_array).T
        return vertices_sites_results_array

    def get_intersected_voxel_volume_ratio(self, all_voxel_assignments):
        charge_grid = self.charge_grid
        partitioning = self.partitioning
        unit_cell_permutations_frac = self.unit_cell_permutations_frac

        all_site_voxel_assignments = all_voxel_assignments.copy()
        # Get voxel fracs for voxels that haven't been assigned
        multi_site_voxel_indices = np.where(all_site_voxel_assignments == 0)[0]

        voxel_vertices_frac_coords_stack = self.get_voxel_vertices_frac_coords_stack(
            multi_site_voxel_indices
        )
        voxel_vertices_frac_coords = np.array_split(voxel_vertices_frac_coords_stack, 8)
        voxel_vertices_cart_coords_stack = (
            charge_grid.get_cart_coords_from_frac_full_array(
                voxel_vertices_frac_coords_stack
            )
        )
        voxel_vertices_cart_coords = np.array_split(voxel_vertices_cart_coords_stack, 8)
        # create an array of site results for each vertex. The rows are voxel indices
        # and the columns are vertex indices
        vertices_sites_results_array = self.get_vertices_site_assignments(
            voxel_vertices_frac_coords_stack
        )
        # There are several common occurances in the vertices sites array.
        # 1.  All of the vertices are assigned to one site. This indicates that the
        #     voxel should be entirely assigned to that one site.
        # 2.  All of the vertices fail to be assigned to a site. This might indicate
        #     an error with the partitioning. I'll need to look through this
        # 3.  The vertices are partially assigned to 1 site and partially assigned to
        #     nothing. These should be assigned to the one site.
        # 4.  The vertices are split between two sites. This indicates that they are
        #     split by 1 plane. We need to calculate where the planes intersect the voxel
        #     to calculate the volume assigned to each site
        # 5.  The vertices are split between more than 2 sites. This indicates the voxel
        #     is at a corner. These are passed to another less rigorous step.
        # create lists to store the voxels in each of these situations. A for loop was
        # the fastest way I could think to do this since we require more complicated
        # logic.
        # At the same time, we want to start keeping track of the information we'll need
        # to calculate the fractional volume of each voxel that belongs to a given site.
        # To do this we need to track the two sites in the voxels split by two sites. We
        # also want to create lists for each voxel to store the important sites that will
        # contribute to our convex hull later
        one_site_in_vertices = []
        one_site_in_vertices_indices = []
        two_sites_in_vertices = []
        two_sites_in_vertices_indices = []
        multi_sites_in_vertices_indices = []

        least_prevalent_site_in_vertices = []
        most_prevalent_site_in_vertices = []
        voxel_vertices_and_intersections = []
        for plane_split_voxel_index, row in enumerate(vertices_sites_results_array):
            # get the set of sites in this row
            unique_sites, counts = np.unique(row, return_counts=True)
            non_zeros_indices = np.where(unique_sites != 0)
            unique_sites = unique_sites[non_zeros_indices]
            counts = counts[non_zeros_indices]
            # If there is only one site in the set, there is only one site (or no sites)
            # that all of the voxels were assigned to.
            if len(unique_sites) == 1:
                one_site_in_vertices.append(unique_sites[0])
                one_site_in_vertices_indices.append(plane_split_voxel_index)
            elif len(unique_sites) == 2:
                # We have 1 or two sites. If one of the values is 0 we only actually have
                # one value assigned and append this value to our list of one site
                # voxels. Otherwise we have two sites and append to our two sites
                two_sites_in_vertices.append(unique_sites)
                two_sites_in_vertices_indices.append(plane_split_voxel_index)
                # find which site is the most common and least common and add to
                # our list
                least_common_site = unique_sites[np.argmin(counts)]
                most_common_site = unique_sites[np.argmax(counts)]
                least_prevalent_site_in_vertices.append(least_common_site)
                most_prevalent_site_in_vertices.append(most_common_site)
                # get the vertex indices that have the less common site
                vertices_with_least_common_site = np.where(row == least_common_site)[0]
                # get all of the cartesian coordinates for these vertices
                important_voxel_vertices = []
                for vertex_index in vertices_with_least_common_site:
                    vertex = voxel_vertices_cart_coords[vertex_index][
                        plane_split_voxel_index
                    ]
                    important_voxel_vertices.append(vertex)
                # append these coordinates to a list of coordinates that will be
                # used later to calculate the fraction of each voxel belonging to a site
                voxel_vertices_and_intersections.append(important_voxel_vertices)
            else:
                # We don't have a rigorous way of handling voxels split by more than
                # one plane so we pass this to the next step of the algorithm
                multi_sites_in_vertices_indices.append(plane_split_voxel_index)
        # convert our list of voxels with two sites to an array then find the unique
        # pairs of sites
        one_site_in_vertices = np.array(one_site_in_vertices)
        one_site_in_vertices_indices = np.array(one_site_in_vertices_indices).astype(
            int
        )
        one_site_in_vertices_original_indices = multi_site_voxel_indices[
            one_site_in_vertices_indices
        ]
        two_sites_in_vertices = np.array(two_sites_in_vertices)
        two_sites_in_vertices_indices = np.array(two_sites_in_vertices_indices).astype(
            int
        )
        two_sites_in_vertices_unique = np.unique(two_sites_in_vertices, axis=0)
        least_prevalent_site_in_vertices = np.array(least_prevalent_site_in_vertices)
        most_prevalent_site_in_vertices = np.array(most_prevalent_site_in_vertices)
        print(len(two_sites_in_vertices_indices))
        # get original voxel indices for each site split by two planes
        two_sites_in_vertices_original_indices = multi_site_voxel_indices[
            two_sites_in_vertices_indices
        ]
        # multi_sites_in_vertices_original_indices = multi_site_voxel_indices[
        #     multi_sites_in_vertices_indices]

        # Now that we have a list of unique site pairs, we want to find which voxels
        # fall into these unique pairs. We do this because we will iterate over each
        # of these pairs to limit the number of planes that need to be checked for
        # intersection with the planes
        two_sites_in_vertices_unique_indices = []
        two_sites_in_vertices_unique_original_indices = []
        for site_pairs in two_sites_in_vertices_unique:
            # get the indices in our array of voxels split by one plane at which each
            # unique pair of sites is found
            sub_indices = np.where((two_sites_in_vertices == site_pairs).all(axis=1))[0]
            # get the indices in the total array of voxels that were near a plane (or
            # not found to belong to a site)
            indices = two_sites_in_vertices_indices[sub_indices]
            two_sites_in_vertices_unique_indices.append(sub_indices)
            two_sites_in_vertices_unique_original_indices.append(indices)
            # get the indices in the original array containing all of the voxels
            original_indices = multi_site_voxel_indices[indices]

        edge_vectors = self.voxel_edge_vectors

        # Now we want to loop over our unique plane pairs to only focus on planes of
        # interest
        for site_pair, original_indices, double_site_indices in zip(
            two_sites_in_vertices_unique,
            two_sites_in_vertices_unique_original_indices,
            two_sites_in_vertices_unique_indices,
        ):
            # We get the important planes from our partitioning dataframes. We also
            # remove any planes that are unrelated to our site pair
            sites = site_pair - 1
            plane_points = []
            plane_vectors = []
            # Now we want to get only the planes that are between the sites of interest.
            # We get the partitioning for the first site then find the planes that go
            # to the second site
            partitioning1 = partitioning[sites[0]]
            partitioning1 = partitioning1.loc[partitioning1["neigh_index"] == sites[1]]
            plane_points.append(np.array(partitioning1["plane_points"].to_list()))
            plane_vectors.append(np.array(partitioning1["plane_vectors"].to_list()))
            # Now we repeat for the second site
            partitioning2 = partitioning[sites[1]]
            partitioning2 = partitioning2.loc[partitioning2["neigh_index"] == sites[0]]
            plane_points.append(np.array(partitioning1["plane_points"].to_list()))
            plane_vectors.append(np.array(partitioning1["plane_vectors"].to_list()))
            plane_points = np.concatenate(plane_points)
            plane_vectors = np.concatenate(plane_vectors)
            # get the dot products between the edges and the plane vectors. This is a
            # 2D array with indices (i,j) where i is the edge index and j is the plane
            # index
            edge_plane_dot_prods = self.calculate_t_den(plane_vectors)

            # We want to make one large array of all possible edges and unit_cell_permutations_frac
            # for this set of vertices. Then we can calculate t for all of them at once.
            # We also need to transform any intersections back to the original coords of
            # the voxel
            #!!! These calculations could be reduced further I think by using the same
            # starting vertex for as many edges as possible. Then the t_numerator array
            # would need to be expanded afterwards

            all_vertex_frac_coords = []
            for transformation in unit_cell_permutations_frac:
                # We iterate only through the first indices of the edges because the
                # t numerator only depends on this value. This means we decrease from
                # 12 edges to 4 points
                for A in [0, 3, 5, 6]:
                    # select the appropriate vertex. This is equivalent to A in our
                    # line segment equation so it should be the first index for each edge
                    vertex = A
                    vertex_frac_coords = voxel_vertices_frac_coords[vertex][
                        original_indices
                    ]
                    # Loop over all tranformations and append to one big array to calculate
                    # all at once
                    new_vertex_frac_coords = vertex_frac_coords.copy()
                    x1, y1, z1 = transformation
                    new_vertex_frac_coords[:, 0] += x1
                    new_vertex_frac_coords[:, 1] += y1
                    new_vertex_frac_coords[:, 2] += z1
                    all_vertex_frac_coords.append(new_vertex_frac_coords)
            all_vertex_frac_coords = np.concatenate(all_vertex_frac_coords)
            # convert to cartesian coords
            all_vertex_cart_coords = charge_grid.get_cart_coords_from_frac_full_array(
                all_vertex_frac_coords
            )

            # Now we calculate the numerateor of the line segment t variable for each
            # vertex plane pair. The array will have plane indices as columns.
            # The rows will be the voxel index*edge_index*vertex_index
            #!!! I currently don't check for memory usage here. I may need to start
            # doing this in chunks if there are memory issues
            t_numerator = self.calculate_t_num(
                all_vertex_cart_coords, plane_points, plane_vectors
            )
            # now we need to replicate each part of the t numerator corresponding to a
            # given point A 3 times. This will get us back to the appropriate number of edges
            t_numerator = np.split(t_numerator, 27 * 4)
            t_numerator = [np.tile(chunk, (3, 1)) for chunk in t_numerator]
            t_numerator = np.concatenate(t_numerator)
            # do the same for the cart coords we calculated
            all_vertex_cart_coords = np.split(all_vertex_cart_coords, 27 * 4)
            all_vertex_cart_coords = [
                np.tile(chunk, (3, 1)) for chunk in all_vertex_cart_coords
            ]
            all_vertex_cart_coords = np.concatenate(all_vertex_cart_coords)
            # Now we need to create a t_denomenator array.
            t_denomenator = np.repeat(
                edge_plane_dot_prods, len(original_indices), axis=0
            )
            t_denomenator = np.tile(t_denomenator, (27, 1))
            t = t_numerator / t_denomenator
            # find where t is between 0 and 1 indicating that the edge in intersected
            t_important = np.where((t >= 0) & (t <= 1))
            # get the t values at the important indices and the cartesian coords of the
            # vertex of interest. Then calculate the intercepts
            t_values = t[t_important]
            important_vertex_cart_coords = all_vertex_cart_coords[t_important[0]]
            # Get new array of proper edges for each vertex, permutation, edge combination
            all_vertex_edge_vectors = np.repeat(
                edge_vectors, len(original_indices), axis=0
            )
            all_vertex_edge_vectors = np.tile(all_vertex_edge_vectors, (27, 1))
            important_edge_vectors = all_vertex_edge_vectors[t_important[0]]
            # calculate all intercepts
            intercepts = (
                important_vertex_cart_coords
                + t_values[:, np.newaxis] * important_edge_vectors
            )
            # now we need to transform the intercepts to the positions of the voxels so
            # that the volume fraction can be calculated properly
            unit_cell_permutations_cart = (
                charge_grid.get_cart_coords_from_frac_full_array(
                    unit_cell_permutations_frac
                )
            )

            intercept_all_vertex_indices = []
            transformed_intercepts = []
            for i, transformation in enumerate(unit_cell_permutations_cart):
                # get indices of the full list of vertices after all transformations at
                # which this transformation was applied
                chunk_size = len(all_vertex_cart_coords) / 27
                first_index = int(chunk_size * i)
                final_index = int(first_index + chunk_size - 1)
                intercept_indices = np.where(
                    (t_important[0] >= first_index) & (t_important[0] <= final_index)
                )[0]
                # Get the array of indices for the full cartesian coords list
                full_list_index = t_important[0][intercept_indices]
                intercept_all_vertex_indices.append(full_list_index)
                # Get the cartesian coordinates of each intercept
                intercept_cart_coords = intercepts[intercept_indices]
                # Transform the intercept back to the original voxel position
                new_intercept_cart_coords = intercept_cart_coords.copy()
                x1, y1, z1 = transformation
                new_intercept_cart_coords[:, 0] -= x1
                new_intercept_cart_coords[:, 1] -= y1
                new_intercept_cart_coords[:, 2] -= z1
                transformed_intercepts.append(new_intercept_cart_coords)
            # concatenate all transformed coordinates and indices
            intercept_all_vertex_indices = np.concatenate(intercept_all_vertex_indices)
            transformed_intercepts = np.concatenate(transformed_intercepts)
            # calculate the original indices for these voxels
            intercept_reduced_site_pair_indices = intercept_all_vertex_indices % len(
                double_site_indices
            )
            # append transformed intersections to appropriate sites
            intercept_originaltwo_site_indices = double_site_indices[
                intercept_reduced_site_pair_indices
            ]
            for original_site_index, intercept in zip(
                intercept_originaltwo_site_indices, transformed_intercepts
            ):
                voxel_vertices_and_intersections[original_site_index].append(intercept)

        frac_volumes = []
        for points in voxel_vertices_and_intersections:
            try:
                hull = ConvexHull(points)
                frac_volumes.append(hull.volume)
            except:
                frac_volumes.append(0)

        frac_volumes = np.array(frac_volumes)
        frac = frac_volumes / (
            charge_grid.structure.volume / np.prod(charge_grid.grid_shape)
        )
        frac = frac.round(12)
        inv_frac = 1 - frac
        # create an array for the results of planes split by two sites. The
        # columns represent the voxel index, fraction of voxel belonging to the
        # first site, frac of voxel belonging to second site, the first site index
        # and the second site index
        two_sites_results_array = np.column_stack(
            (
                two_sites_in_vertices_original_indices,
                frac,
                inv_frac,
                least_prevalent_site_in_vertices,
                most_prevalent_site_in_vertices,
            )
        )
        # Now we want to add the voxels where all of the vertices pointed to
        # the same site.
        one_site_fracs = np.ones(len(one_site_in_vertices))
        one_site_least_prevalent_site = np.zeros(len(one_site_in_vertices))
        one_site_results_array = np.column_stack(
            (
                one_site_in_vertices_original_indices,
                one_site_least_prevalent_site,
                one_site_fracs,
                one_site_least_prevalent_site,
                one_site_in_vertices,
            )
        )
        # combine the results into one
        results_array = np.concatenate(
            (two_sites_results_array, one_site_results_array)
        )
        # Now we want to make an array with all voxel assignments as integers.
        # this will allow us to print the voxels belonging primarily to different
        # atoms. first get the indices where each site is more prevalent
        least_prevalent_indices = np.where(results_array[:, 1] > 0.5)[0]
        most_prevalent_indices = np.where(results_array[:, 2] > 0.5)[0]
        mixed_indices = np.where(results_array[:, 1] == 0.5)[0]

        least_prevalent_indices_original = results_array[:, 0][
            least_prevalent_indices
        ].astype(int)
        most_prevalent_indices_original = results_array[:, 0][
            most_prevalent_indices
        ].astype(int)
        # update the site voxel assignments with the more prevalent site
        all_site_voxel_assignments[least_prevalent_indices_original] = results_array[
            :, 3
        ][least_prevalent_indices]
        all_site_voxel_assignments[most_prevalent_indices_original] = results_array[
            :, 4
        ][most_prevalent_indices]
        # now we want to randomly assign the voxels that were split exactly
        random_float = np.random.rand(len(mixed_indices))
        random_float_below = np.where(random_float <= 0.5)[0]
        random_float_above = np.where(random_float > 0.5)[0]
        all_site_voxel_assignments[
            results_array[:, 0].astype(int)[mixed_indices][random_float_below]
        ] = results_array[:, 3][mixed_indices[random_float_below]]
        all_site_voxel_assignments[
            results_array[:, 0].astype(int)[mixed_indices][random_float_above]
        ] = results_array[:, 4][mixed_indices[random_float_above]]
        # We now have array with a single atom assignments for all voxels with
        # one or two assignments. We want to find the results for any remaining
        # voxels split by more that two planes

        (
            multi_site_voxel_assignments,
            all_site_voxel_assignments,
        ) = self.get_voxels_multi_planes(all_site_voxel_assignments)
        all_site_voxel_assignments_grid = all_site_voxel_assignments.reshape(
            charge_grid.grid_shape
        )

        return (
            results_array,
            multi_site_voxel_assignments,
            all_site_voxel_assignments_grid,
        )

    def get_voxels_multi_planes(self, all_voxel_assignments):
        logging.info("Finding sites for voxels split by more than one plane.")
        charge_grid = self.charge_grid
        grid_shape = charge_grid.grid_shape
        all_site_assignment_grid = all_voxel_assignments.reshape(charge_grid.grid_shape)
        unassigned_voxels = np.where(all_site_assignment_grid == 0)
        electride_sites = self.electride_sites
        indices = []
        all_sites = []
        all_fracs = []
        for x, y, z in zip(
            unassigned_voxels[0], unassigned_voxels[1], unassigned_voxels[2]
        ):
            index = int(x + y * grid_shape[1] + z * grid_shape[1] * grid_shape[0])
            indices.append(index)
            sites = []
            for t, u, v in itertools.product([-1, 0, 1], [-1, 0, 1], [-1, 0, 1]):
                new_idx = [x - 1 + t, y - 1 + u, z - 1 + v]

                # wrap around for voxels on edge of cell
                new_idx = [a % b for a, b in zip(new_idx, grid_shape)]
                site = all_site_assignment_grid[new_idx[0], new_idx[1], new_idx[2]]
                if site not in electride_sites and site != 0:
                    sites.append(site)
            if len(sites) > 0:
                unique_sites, counts = np.unique(sites, return_counts=True)
                fracs = np.array([count / len(sites) for count in counts])
            else:
                cart_coord = charge_grid.get_cart_coords_from_vox([x + 1, y + 1, z + 1])
                site = self.get_voxels_site_nearest(cart_coord)
                unique_sites = np.array([site])
                fracs = np.array([1])
            most_prevalent_site = unique_sites[np.where(fracs == np.max(fracs))[0]][0]
            # update all_voxel_assignments
            all_voxel_assignments[index] = most_prevalent_site
            all_sites.append(unique_sites)
            all_fracs.append(fracs)
        # print(f"Used {num_nearest_sites} nearest sites")
        results_dict = {"indices": indices, "sites": all_sites, "fracs": all_fracs}
        return results_dict, all_voxel_assignments

    def get_voxels_site_nearest(
        self,
        point_voxel_coords: ArrayLike | list,
    ):
        if self.algorithm == "badelf":
            structure = self.charge_grid.structure
        elif self.algorithm == "voronelf":
            structure = self.electride_structure
        structure_temp = structure.copy()
        structure_temp.append("He", point_voxel_coords, coords_are_cartesian=True)
        nearest_site = structure_temp.get_neighbors(structure_temp[-1], 5)[0].index
        nearest_site += 1
        # create dictionary for recording what fraction of a voxels volume should
        # be associated with a given site.
        return nearest_site
