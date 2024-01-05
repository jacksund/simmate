# -*- coding: utf-8 -*-

import math

import numpy as np
from pymatgen.analysis.local_env import CrystalNN

from simmate.apps.badelf.core.grid import Grid
from simmate.apps.badelf.core.partitioning import PartitioningToolkit


class ElectrideFinder:
    """
    A class for finding electride sites from an ELFCAR.

    Args:
        grid : Grid
            A BadELF app Grid instance made from an ELFCAR.
    """

    def __init__(
        self,
        grid: Grid,
    ):
        self.grid = grid.copy()

    def gaussian_fit(coordinates, amplitude, x0, y0, z0, sigma_x, sigma_y, sigma_z):
        x, y, z = coordinates
        return amplitude * np.exp(
            -((x - x0) ** 2 / (2 * sigma_x**2))
            - ((y - y0) ** 2 / (2 * sigma_y**2))
            - ((z - z0) ** 2 / (2 * sigma_z**2))
        )

    def find_local_maxima(self, neighborhood_size=1, threshold=None):
        """
        Find local maxima in a 3D numpy array.

        Args:
        - neighborhood_size: Size of the neighborhood for finding local maxima
        - threshold: Threshold for considering a point as a local maximum

        Returns:
        - List of tuples containing the coordinates of local maxima
        """
        grid = self.grid.copy()
        grid.regrid(desired_resolution=1000)
        elf_data = grid.total
        # Get padded data so that we can look at voxels at the edges
        padded_elf_data = np.pad(elf_data, neighborhood_size, mode="wrap")
        maxima_cart_coords = []
        maxima_values = []

        # Look across each voxel in the structure.
        for z in range(neighborhood_size, padded_elf_data.shape[0] - neighborhood_size):
            for y in range(
                neighborhood_size, padded_elf_data.shape[1] - neighborhood_size
            ):
                for x in range(
                    neighborhood_size, padded_elf_data.shape[2] - neighborhood_size
                ):
                    # Get a section of the dataframe around the voxel
                    neighborhood = padded_elf_data[
                        z - neighborhood_size : z + neighborhood_size + 1,
                        y - neighborhood_size : y + neighborhood_size + 1,
                        x - neighborhood_size : x + neighborhood_size + 1,
                    ]
                    # Get the max value in the neighborhood
                    max_value = np.max(neighborhood)
                    z_orig = z - neighborhood_size
                    y_orig = y - neighborhood_size
                    x_orig = x - neighborhood_size
                    # If the maximum value is at the voxel we're looking at, this
                    # is a maximum and we add the cartesian coordinates and value
                    # to our list
                    if elf_data[z_orig, y_orig, x_orig] == max_value and (
                        threshold is None or max_value > threshold
                    ):
                        maxima_voxel_coord = (z_orig + 1, y_orig + 1, x_orig + 1)
                        maxima_cart_coord = grid.get_cart_coords_from_vox(
                            maxima_voxel_coord
                        )
                        maxima_cart_coords.append(maxima_cart_coord)
                        maxima_values.append(elf_data[z_orig, y_orig, x_orig])

        return maxima_cart_coords, maxima_values

    def get_electride_structure(
        self,
        local_maxima_coords: list = None,
        local_maxima_values: list = None,
        remove_old_electrides: bool = False,
        distance_cutoff: float = 1.6,
        electride_finder_cutoff: float = 0.5,
        min_electride_radius: float = 0.8,
    ):
        #!!! The distance cutoff and min_electride_radius are fairly arbitrary
        # How should I find them instead?
        """
        Finds the electrides in a structure using an ELF grid.

        Parameters
        ----------
        local_maxima_coords : list, optional
            The coordinates of all local maxima in the grid. This will be found
            automatically if not set.
        local_maxima_values : list, optional
            The values at the local maxima. This will be found automatically if
            not set.
        remove_old_electrides : bool, optional
            Whether or not to remove any other electrides already placed in
            the system. It is generally recommended that structures without
            electrides are provided.
        distance_cutoff : float, optional
            The minimum distance the local maxima must be from an atom to be
            considered as a possible electride. The default is 1.19.
        elf_cutoff : float, optional
            The minimum elf value at the site to be considered a possible
            electride. The default is 0.5.
        min_electride_radius : float, optional
            The minimum elf radius around the maximum for it to be considered
            an electride. The default is 1.19 which is the radius of fluoride
            in a 6 coordination environment.

        Returns
        -------
        A structure object with the found electride sites labeled with "He"
        dummy atoms.
        """
        grid = self.grid.copy()
        if local_maxima_coords is None:
            local_maxima_coords, local_maxima_values = self.find_local_maxima()

        structure = grid.structure
        if "He" in structure.symbol_set and remove_old_electrides:
            old_electride_sites = structure.indices_from_symbol("He")
            structure.remove_sites(old_electride_sites)

        cnn = CrystalNN()
        electride_coords = []
        for i, maximum_coords in enumerate(local_maxima_coords):
            # Check if the elf value is below the cutoff
            if local_maxima_values[i] < electride_finder_cutoff:
                continue

            electride_structure = structure.copy()
            electride_structure.append("He", maximum_coords, coords_are_cartesian=True)
            _, _, electride_neighbors = cnn.get_nn_data(electride_structure, n=-1)

            most_neighbors = max(electride_neighbors)
            electride_neighbors = electride_neighbors[most_neighbors]
            # get distances to nearby atoms
            atom_distances = []
            for neighbor in electride_neighbors:
                if neighbor["site"].species_string != "He":
                    distance = math.dist(maximum_coords, neighbor["site"].coords)
                    atom_distances.append(distance)

            # check if minimum distance is too close to an atom:

            if min(atom_distances) < distance_cutoff:
                continue

            # get distances to min along lines to closest atoms
            electride_grid = grid.copy()
            electride_grid.structure = electride_structure
            electride_radius = PartitioningToolkit(electride_grid).get_elf_ionic_radius(
                site_index=len(electride_structure) - 1,
                structure=electride_structure,
            )
            # print(f"{maximum_coords} {min(atom_distances)} {electride_radius}")
            if electride_radius < min_electride_radius:
                continue

            # If the loop is still going, we consider this site an electride. We
            # add it to the list of electride sites.
            electride_coords.append(maximum_coords)
            # electride_coordinations.append(cnn.get_cn(electride_structure, n=-1))

        # Add our potential electride sites to our structure
        electride_structure = structure.copy()
        for coord in electride_coords:
            electride_structure.append("He", coord, coords_are_cartesian=True)

        # Often the algorithm will find several electride sites right next to
        # eachother. This can be due to voxelation or because of oddly shaped
        # electrides. We want to combine these into one electride site.
        electride_structure.merge_sites(tol=0.5, mode="average")

        return electride_structure
