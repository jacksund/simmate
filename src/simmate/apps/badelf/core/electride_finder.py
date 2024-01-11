# -*- coding: utf-8 -*-
import logging
import math
from functools import cached_property
from pathlib import Path

import numpy as np
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.core.periodic_table import _pt_data as pt_data
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from simmate.apps.badelf.core.grid import Grid
from simmate.apps.badelf.core.partitioning import PartitioningToolkit
from simmate.apps.bader.outputs import ACF
from simmate.workflows.utilities import get_workflow


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
        directory: Path,
    ):
        self.grid = grid.copy()
        self.directory = directory

    @cached_property
    def local_maxima(self):
        """
        The local maxima in a 3D numpy array
        """
        return self.find_local_maxima()

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

    @staticmethod
    def to_number_from_roman_numeral(roman_num):
        lookup = {
            "X": 10,
            "V": 5,
            "I": 1,
        }
        total = 0
        i = 0
        while i < len(roman_num):
            # If this is the subtractive case.
            if (
                i + 1 < len(roman_num)
                and lookup[roman_num[i]] < lookup[roman_num[i + 1]]
            ):
                total += lookup[roman_num[i + 1]] - lookup[roman_num[i]]
                i += 2
            # Else this is NOT the subtractive case.
            else:
                total += lookup[roman_num[i]]
                i += 1

        return total

    @cached_property
    def shannon_radii_estimate(self):
        """
        Gets the shannon crystal radii for each atom in the structure. The
        oxidation states are estimated using traditional bader.
        """
        directory = self.directory
        structure = self.grid.structure
        badelf_workflow = get_workflow("population-analysis.bader.bader-dev")
        badelf_workflow.run(
            directory=directory,
        )

        # Get oxidation states for each atom as a list
        results_dataframe, extra_data = ACF(directory)
        oxidation_states = results_dataframe.oxidation_state.values
        oxidation_states = np.round(oxidation_states)
        # add method to get coordination environments. This already exists in
        # badelftoolkit but I don't want to repeat it for no reason.
        cnn = CrystalNN()
        shannon_radii = {}
        for site_index, site in enumerate(structure):
            # We need the shannon radii data for the atom we're investigating.
            # We get this from pymatgen's pt_data dictionary
            site_species = structure[site_index].species_string
            species_dict = pt_data[site_species]["Shannon radii"]

            # Now we need the oxidation state and coordination environment of
            # our atom of interest in order to get the closest matching shannon
            # radius. For electrides we'll often get estimated oxidation states
            # that are far from accurate, so we get the closest available radius
            oxidation_state = oxidation_states[site_index]
            coord_env = cnn.get_cn(structure, site_index)

            available_ox_state = species_dict.keys()
            # We find the closest oxidation state to the one we got from bader.
            # The min function here is taking in the available oxidation values.
            # It then looks at every available oxidation state (x) and calculates
            # the difference between it and the bader ox value and stores it as
            # a key. It then returns the available oxidation state with the lowest
            # key value.
            closest_ox_state = min(
                available_ox_state, key=lambda x: abs(int(x) - oxidation_state)
            )

            available_coord_envs = species_dict[closest_ox_state].keys()
            # We similarly find the closest coordination env. These are stored
            # as roman numerals in the pymatgen pt_data so they must be converted
            # to integers
            closest_coord_env = min(
                available_coord_envs,
                key=lambda x: abs(self.to_number_from_roman_numeral(x) - coord_env),
            )

            # We now get the closest shannon prewitt crystal radius
            shannon_radius = species_dict[closest_ox_state][closest_coord_env][""][
                "crystal_radius"
            ]
            shannon_radii[site_index] = shannon_radius
        return shannon_radii

    @cached_property
    def elf_radii(self):
        """
        Gets the elf radius of each atom in the structure
        """
        grid = self.grid.copy()
        structure = grid.structure.copy()
        # We don't want to find the radius for every atom in the structure if
        # there is symmetry. We instead find the radius for each unique atom
        symmetry_dataset = SpacegroupAnalyzer(structure).get_symmetry_dataset()
        equivalent_atoms = symmetry_dataset["equivalent_atoms"]

        # We now have an array of the same length as the structure. Each value
        # in the array is an int pointing to the first equivalent atom in the
        # structure if it exists (or itself if its the earliest equivalent one).
        # Now we want to get the ELF radius for each unique atom. We iterate over
        # each unique atom to get its radius and add it to a dictionary.
        unique_atoms = np.unique(equivalent_atoms)
        unique_atom_radii = {}
        for atom in unique_atoms:
            radius = PartitioningToolkit(grid).get_elf_ionic_radius(
                site_index=atom,
                structure=structure,
            )
            unique_atom_radii[atom] = radius

        # We now construct a dictionary for all of the atoms in the structure
        # that provides its radius
        all_atom_radii = {}
        for site_index, site in enumerate(structure):
            equiv_atom = equivalent_atoms[site_index]
            radius = unique_atom_radii[equiv_atom]
            all_atom_radii[site_index] = radius

        return all_atom_radii

    def get_ionic_radii(
        self,
        method="elf",
    ):
        """
        Gets the radius for each atom in the structure.

        Parameters
        ----------

        method : str, optional
            The method used to find the radii. Options are "elf" or "shannon".
            elf will use the provided grid to find the radius of each atom and
            shannon will use bader oxidation states and the closest available
            tabulated shannon crystal radius.
        """
        if method == "elf":
            atom_radii = self.elf_radii
        elif method == "shannon":
            atom_radii = self.shannon_radii_estimate
        else:
            raise ValueError(
                """Selected method for finding ionic radii does not exist. Available
                methods are "elf" and "shannon"
                """
            )
        return atom_radii

    def get_electride_structure(
        self,
        electride_finder_cutoff: float = 0.5,
        min_electride_radius: float = 0.9,
        atom_radius_method: str = "elf",
        remove_old_electrides: bool = False,
        local_maxima_coords: list = None,
        local_maxima_values: list = None,
    ):
        #!!! The min_electride_radius is based off of fluoride, but it feels
        # arbitrary. Is there a better way?
        """
        Finds the electrides in a structure using an ELF grid.

        Parameters
        ----------

        electride_finder_cutoff : float, optional
            The minimum elf value at the site to be considered a possible
            electride. The default is 0.5.
        min_electride_radius : float, optional
            The minimum elf radius around the maximum for it to be considered
            an electride. The default is 0.9 which is somewhat arbitrarily chosen.
            An goold alternative is 1.19 which is the average radius of fluoride
            in a 6 coordination environment.
        atom_radius_method : str, optional
            The method used to find the radii. Options are "elf" or "shannon".
            elf will use the provided grid to find the radius of each atom and
            shannon will use bader oxidation states and the closest available
            tabulated shannon crystal radius.
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

        Returns
        -------
        A structure object with the found electride sites labeled with "He"
        dummy atoms.
        """
        logging.info("Finding electride sites")
        # Get the coordinates and values of each local maximum in the grid
        grid = self.grid.copy()
        if local_maxima_coords is None:
            local_maxima_coords, local_maxima_values = self.local_maxima

        # If there are He atoms that have already been placed in the structure
        # that the user wants to remove, remove them now.
        structure = grid.structure.copy()
        if "He" in structure.symbol_set and remove_old_electrides:
            old_electride_sites = structure.indices_from_symbol("He")
            structure.remove_sites(old_electride_sites)
        elif "He" in structure.symbol_set and not remove_old_electrides:
            logging.warning(
                """
                  Dummy atoms were found already in the structure. No new
                  electride sites will be added. To have the algorithm search
                  for electride sites, remove all He dummy atoms in the structure.
                  """
            )
            return structure

        # Create a list to store the electride coords.
        cnn = CrystalNN()
        electride_coords = []
        # get the estimated shannon radii of each of the sites in the structure.
        # These will be used to estimate electride radii
        shannon_radii = self.get_ionic_radii(atom_radius_method)
        for i, maximum_coords in enumerate(local_maxima_coords):
            # Check if the elf value is below the cutoff
            if local_maxima_values[i] < electride_finder_cutoff:
                continue

            # Create a dummy structure. Add a dummy at the local maximum that
            # was found
            electride_structure = structure.copy()
            electride_structure.append("He", maximum_coords, coords_are_cartesian=True)
            # Get the nearest neighbors of the electride. cnn will return a dict
            # with multiple keys. These might be different methods of finding neighbors?
            # I pick the one with the most neighbors
            _, _, electride_neighbors = cnn.get_nn_data(electride_structure, n=-1)
            most_neighbors = max(electride_neighbors)
            electride_neighbors = electride_neighbors[most_neighbors]

            # get the distance from the potential electride site to the edge
            # of the atoms shannon radius. This is the maximum radius that the
            # electride can have.
            max_electride_radii = []
            for neighbor in electride_neighbors:
                neighbor_index = neighbor["site_index"]
                neighbor_shann_rad = shannon_radii[neighbor_index]
                if neighbor["site"].species_string != "He":
                    distance_to_atom = math.dist(
                        maximum_coords, neighbor["site"].coords
                    )
                    max_radius = distance_to_atom - neighbor_shann_rad
                    max_electride_radii.append(max_radius)

            # check if minimum distance is too close to an atom:

            if min(max_electride_radii) < min_electride_radius:
                continue

            # The following code is another method for finding the radius of the
            # electrides using ELF. It works well in many situations but is
            # less lenient than using the atoms shannon radii. It is kept here
            # in case it becomes more desirable in the future.
            # # get distances to min along lines to closest atoms
            # electride_grid = grid.copy()
            # electride_grid.structure = electride_structure
            # electride_radius = PartitioningToolkit(electride_grid).get_elf_ionic_radius(
            #     site_index=len(electride_structure) - 1,
            #     structure=electride_structure,
            # )
            # if electride_radius < min_electride_radius:
            #     continue

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

        # The above pymatgen method often reorders the atoms in the structure which
        # causes issues down the line. We want to resort the atoms into their
        # original order with electrides at the end. To do this, we create another
        # copy of the original structure and add all of the final electride sites
        final_electride_structure = structure.copy()
        electride_sites = electride_structure.indices_from_symbol("He")
        if len(electride_sites) > 0:
            logging.info(f"{len(electride_sites)} electride sites found")
            for site in electride_sites:
                coord = electride_structure[site].coords
                final_electride_structure.append("He", coord, coords_are_cartesian=True)
        else:
            logging.info("No electride sites found")
        return final_electride_structure
