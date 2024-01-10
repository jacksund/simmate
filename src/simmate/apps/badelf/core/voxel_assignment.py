# -*- coding: utf-8 -*-

import itertools

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from scipy.spatial import ConvexHull

from simmate.apps.badelf.core.grid import Grid
from simmate.apps.badelf.core.partitioning import PartitioningToolkit
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
        partitioning_grid: Grid,
        algorithm: str,
        electride_structure: Structure,
        partitioning: dict,
    ):
        self.partitioning_grid = partitioning_grid.copy()
        self.charge_grid = charge_grid.copy()
        self.algorithm = algorithm
        # partitioning will contain electride sites for voronelf
        self.partitioning = partitioning
        self.electride_structure = electride_structure

    @property
    def permutations(self):
        return self.charge_grid.permutations

    def get_matching_site(
        self,
        point_voxel_coord: ArrayLike | list,
        check_near_plane: bool = True,
    ):
        """
        Determines which atomic site a point belongs to.

        Args:
            point_voxel_coord (ArrayLike): The voxel coordinate of the point of
                interest.
            check_near_plane (bool): Whether or not to return None if the voxel
                might be intercepted by a plane.
        Returns:
            The site index that the point belongs to. Returns -1 if the point
            could be assigned to multiple sites.
        """
        partitioning = self.partitioning
        if check_near_plane:
            max_distance = self.charge_grid.max_voxel_dist
        else:
            # We don't want to check if a voxel is close to a plane. We make
            # the max distance negative so that when we check it's not possible
            # for the distance to be less than it.
            max_distance = -1
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # I've had a bug in the past where more than one site is found for a single
        # voxel. As such, I'm going to temporarily make this function search all
        # sites in case it finds more than one. This bug seemed to be due to incorrect
        # plane selection.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        sites = []
        # Iterate over each site in the lattice
        for site, neighbor_df in partitioning.items():
            matched = True
            # Iterate through each neighbor
            for neigh_index, row in neighbor_df.iterrows():
                # get the minimum point and normal vector which define the plane
                # seperating the sites.
                point = row["plane_points"]
                normal_vector = row["plane_vectors"]
                # If a voxel is on the same side of the plane as the site, then they
                # should have the same sign when their coordinates are plugged into
                # the plane equation (negative).
                # expected_sign = values["sign"]

                # use plane equation to find sign
                site_real_coord = self.charge_grid.get_cart_coords_from_vox(
                    point_voxel_coord
                )
                sign, distance = PartitioningToolkit.get_plane_sign(
                    point, normal_vector, site_real_coord
                )

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

    def get_voxels_site_base(
        self,
        point_voxel_coord: ArrayLike | list,
    ):
        """
        Finds the site a voxel belongs to. Mostly does the same as the
        get_matching_site function, but also checks other possible symmetric locations
        of each site.

        Args:
            point_voxel_coord (ArrayLike): The voxel coordinates of the point
                to find the associated site for.

            site (int): A site index. It is None if the voxel has not already
                been assigned to an electride.

        Returns:
            The site the voxel coordinate is associated with.
        """
        permutations = self.permutations
        # partitioning = self.partitioning
        x, y, z = point_voxel_coord
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # I've had a bug in the past where one voxel returns multiple sites after
        # being translated. I'm going to make this function temporarily go through
        # all sites in case the bug still exists. It will return -1 if the multiple
        # sites are found at the same transformation and it will return -2 if multiple
        # are found across different transformations. This bug seemed to be due to
        # insufficient partitioning plane selection
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        sites = []
        # create dictionary for recording what fraction of a voxels volume should
        # be associated with a given site. We do this so that the format of the
        # output matches the other ones.
        site_vol_frac = {}
        for site in range(len(self.electride_structure)):
            site_vol_frac[site] = float(0)

        for t, u, v in permutations:
            new_voxel_coord = [x + t, y + u, z + v]
            site: int = self.get_matching_site(new_voxel_coord)
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
            site_vol_frac[-2] = float(0)
            return site_vol_frac
        elif len(sites) == 1:
            # there is only one site found so we just return it.
            site_vol_frac[sites[0]] = float(1)
            return site_vol_frac
        else:
            site_vol_frac = None

            # there wasn't any site found so we don't return our site variable which
            # is None
        return site_vol_frac

    def _get_vertex_site(
        self,
        vertex_coords,
    ):
        """
        Finds the site a voxel vertex belongs to and returns the site and the
        transformation that it was found at. Mostly does the same as the
        get_voxels_site_base function, but also returns the transformation.

        Args:
            point_voxel_coord (ArrayLike): The voxel coordinates of the point
                to find the associated site for.

        Returns:
            The site a voxel vertex is assigned to as well as the transformation.
        """
        permutations = self.permutations
        x, y, z = vertex_coords

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
            site: int = self.get_matching_site(
                new_vert_coord,
                check_near_plane=False,
            )
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
            if sites[0] == -1:
                return -1, None
            else:
                return sites[0], translations[0]
        else:
            # there wasn't any site found so we don't return our site variable which
            # is None
            return None, None
        # return site

    def get_voxel_vertices_sites(
        self,
        point_voxel_coord: ArrayLike | list,
    ):
        """
        Takes in the coordinates of a voxel and returns the coordinates of each
        of its vertices and the sites they belong to.

        Args:
            point_voxel_coord (ArrayLike): The voxel coordinates of the point
                to find the associated site for.
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
            vertices_coords[key] = [
                x + x1 for x, x1 in zip(point_voxel_coord, transform)
            ]

        # create a dataframe to store results in
        vertices_sites = pd.DataFrame(columns=["id", "transform", "site"])

        # now that we have the coordinates for each vertex, get the site and the
        # transform required to get the site
        for key, coord in vertices_coords.items():
            # try:
            site, transform = self._get_vertex_site(vertex_coords=coord)
            vertex_row = [key, transform, site]
            vertices_sites.loc[len(vertices_sites.index)] = vertex_row
            # If we can't find a site, return an empty row for this key
            # except:
            #     vertex_row = [key, None, None]
            #     vertices_sites.loc[len(vertices_sites.index)] = vertex_row
        # return both the vertices coords and the information about their sites
        return vertices_coords, vertices_sites

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

    def _get_voxel_plane_intersections(
        self,
        sites: list,
        vertices_coords: dict,
        intersections_df: pd.DataFrame,
    ):
        """
        Function for finding which planes intersect a voxel. Returns dataframe
        with all planes and intersections.

        Args:
            sites (list): A list of sites that the vertices of a voxel are assigned to.

            vertices_coords (dict): A dictionary relating the coordinates of a
                voxels vertices to their label.

            intersections_df (Dataframe): A dataframe of intersections that have
                already been found.

        Returns:
            A dataframe of where planes intersect the edges of a voxel.

        """
        partitioning = self.partitioning
        # Define the indices of the vertices making up the edges of the voxel.
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
        # We create a list of sites that we want to allow in the plane intersections
        # search. Each plane is stored twice: once for each atom in the pair. Because
        # of this we remove each site after we've looked at its planes to remove
        # redundancy
        sites_to_search = sites["site"].to_list()
        for site in sites["site"]:
            sites_to_search.remove(site)
            # iterate over each plane
            for neighbor_df_index, row in partitioning[site].iterrows():
                neighbor_index = row["neigh_index"]
                # if neighbor is in the list of sites, look at the plane
                if neighbor_index in sites_to_search:
                    plane_point = row["plane_points"]
                    plane_vector = row["plane_vectors"]
                    # iterate over each edge and find the points that intersect
                    intersections = []
                    for edge in edges:
                        point0 = vertices_coords[edge[0]]
                        point1 = vertices_coords[edge[1]]
                        intersection = self._get_vector_plane_intersection(
                            point0, point1, plane_point, plane_vector
                        )
                        if intersection is not None:
                            # we transform all intersections to be relative to A0 being
                            # the origin. This is so planes from various transformations
                            # can be treated at the same time
                            # MUST ROUND!
                            intersection = [
                                round((x - x1), 12)
                                for x, x1 in zip(intersection, vertices_coords["A0"])
                            ]
                            intersections.append(intersection)
                    if len(intersections) > 0:
                        # if we have any intersections we add the site index, its
                        # neighbors index, and the list of intersections to the df
                        plane_row = [site, row["neigh_index"], intersections]
                        intersections_df.loc[len(intersections_df)] = plane_row
        return intersections_df

    def get_intersected_voxel_volume_ratio(
        self,
        point_voxel_coord: ArrayLike | list,
    ):
        """
        Takes in the coordinates of a voxel and returns the ratio of the voxel
        that belongs to the sites around it.

        Args:
            point_voxel_coord (ArrayLike): The voxel coordinates of the point
                to find the associated site for.
        """
        grid = self.charge_grid.copy()
        voxel_volume = grid.voxel_volume
        vertices_coords, vertices_sites = self.get_voxel_vertices_sites(
            point_voxel_coord
        )

        # create dictionary for recording what fraction of a voxels volume should
        # be associated with a given site.
        site_vol_frac = {}
        for site in range(len(self.electride_structure)):
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
        # try:
        voxel_site, transform = self._get_vertex_site(
            point_voxel_coord,
        )
        # except:
        #     voxel_site, transform = None, None

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
                    real_coord = self.charge_grid.get_cart_coords_from_vox(new_coord)
                    transformed_coords_real[key] = real_coord
                # get any intersections between planes and voxel edges and add to
                # our intersection dataframe
                intersections_df = self._get_voxel_plane_intersections(
                    sites, transformed_coords_real, intersections_df
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
            transformed_coord = [
                x - x1 + 1 for x, x1 in zip(coord, vertices_coords["A0"])
            ]
            # add the real coord to our dictionary of vertices
            vertices_coords_real_origin[key] = grid.get_cart_coords_from_vox(
                transformed_coord
            )

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
                            if np.allclose(
                                intersect_array, site_array, rtol=0, atol=1e-6
                            ):
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
                        print(f"Error with hull: {point_voxel_coord}")
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

    def get_voxels_multi_plane(
        self,
        point_voxel_coords: ArrayLike | list,
        site_vol_frac: dict,
        voxel_assignments: pd.DataFrame,
    ):
        """
        This function finds what sites a voxel divided by more than one plane should
        be applied to. It looks at nearby voxels and finds what sites they are applied
        to and finds the ratio between these sites.
        """
        if site_vol_frac is None:
            x, y, z = point_voxel_coords
            grid_shape = self.charge_grid.grid_shape
            electride_sites = self.electride_sites
            # create dictionary for counting number of sites and for the fraction
            # of sites
            site_count = {}
            site_vol_frac = {}
            for site in range(len(self.electride_structure)):
                site_count[site] = 0
                site_vol_frac[site] = 0
            # look at all neighbors around the voxel of interest
            for t, u, v in itertools.product([-1, 0, 1], [-1, 0, 1], [-1, 0, 1]):
                new_idx = [x - 1 + t, y - 1 + u, z - 1 + v]

                # wrap around for voxels on edge of cell
                new_idx = [a % b for a, b in zip(new_idx, grid_shape)]

                # get site ditionary from the neighboring voxel using its row
                # index. This is much faster than searching by values. To get the index
                # we can utilize the fact that an increase in z will increase the index
                # by 1, an increase in y will increase the index by (range of z),
                # and an increase in x will increase the index by (range of z)*(range of y)
                zrange = grid_shape[2]
                yrange = grid_shape[1]
                index = int(
                    (new_idx[0]) * zrange * yrange + (new_idx[1]) * zrange + new_idx[2]
                )
                site_dict = voxel_assignments["site"].iloc[index]
                # If the site dict exists, we want to look at each of its key/item
                # pairs. -1,-2,-3 indicate some error in voxel assignment. We skip
                # these for now. Also, if the algorithm is "badelf" we don't want to
                # assign anything to electride sites so we also sip thee. Otherwise
                # we add the fraction of each voxel to the voxel count
                #!!! avoiding electrides is going to cause problems for voronelf
                if site_dict is not None:
                    for site_index, frac in site_dict.items():
                        if site_index in [-3, -2, -1]:
                            continue
                        elif (
                            site_index in electride_sites and self.algorithm == "badelf"
                        ):
                            continue
                        else:
                            site_count[site_index] += frac

            if sum(site_count.values()) != 0:
                # get the fraction of each site. This will allow us to split the
                # charge of the voxel more evenly
                for site_index in site_count:
                    site_vol_frac[site_index] = site_count[site_index] / sum(
                        site_count.values()
                    )

            else:
                #  of the voxels nearby returned either None, as an error, or as
                # an electride. To assign this voxel we just give it to the closest
                # atom
                site_vol_frac = self.get_voxels_site_nearest(point_voxel_coords)
        return site_vol_frac

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
        # create dictionary for recording what fraction of a voxels volume should
        # be associated with a given site.
        site_vol_frac = {}
        for site in range(len(self.electride_structure)):
            site_vol_frac[site] = float(0)
        site_vol_frac[nearest_site] = float(1)

        return site_vol_frac

    def get_voxels_site(
        self,
        point_voxel_coords: ArrayLike | list,
        site_vol_frac,
    ):
        """
        Combines methods of voxel assignment to guarantee that the voxel
        site is returned.
        """
        if site_vol_frac is None:
            site_vol_frac = self.get_voxels_site_base(point_voxel_coords)
        if site_vol_frac is None:
            site_vol_frac = self.get_intersected_voxel_volume_ratio(point_voxel_coords)

        return site_vol_frac

    def _get_voxels_site_dask(
        self,
        voxel_dataframe: pd.DataFrame,
    ):
        """
        Applies the get_intersected_voxel_volume_ratio function across a Pandas
        dataframe. This is the function that we give to dasks map_partitions
        function to parallelize voxel assignment.

        Args:
            voxel_dataframe (pd.DataFrame): A dataframe consisting of columns
            [x,y,z] representing the voxels of a system.

        Returns:
            A series of dictionaries containing the ratio of each voxel assigned
            to each site.
        """
        return voxel_dataframe.apply(
            lambda x: self.get_voxels_site(
                [x["x"], x["y"], x["z"]],
                x["site"],
            ),
            axis=1,
        )
