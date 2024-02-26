# -*- coding: utf-8 -*-
import logging
import warnings
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

    def find_local_maxima(self, neighborhood_size: int = 2, threshold: float = 0.5):
        """
        Find local maxima in a 3D numpy array.

        Args:
            neighborhood_size (int):
                Size of the neighborhood for finding local maxima
            threshold (float):
                Threshold for considering a point as a local maximum

        Returns:
            List of tuples containing the fractional coordinates of local maxima
        """
        grid = self.grid.copy()
        # grid.regrid(desired_resolution=1000)
        elf_data = grid.total
        # Get padded data so that we can look at voxels at the edges
        padded_elf_data = np.pad(elf_data, neighborhood_size, mode="wrap")
        maxima_vox_coords = []
        maxima_values = []
        # Get voxel coords where the value is above the threshold
        above_thresh_indices = np.where(elf_data > threshold)
        above_thresh_data = elf_data[above_thresh_indices]
        # Convert to padded indices in an array to loop over
        above_thresh_indices = np.column_stack(above_thresh_indices) + neighborhood_size
        for (x, y, z), data_value in zip(above_thresh_indices, above_thresh_data):
            # Get a section of the dataframe around the voxel
            neighborhood = padded_elf_data[
                x - neighborhood_size : x + neighborhood_size + 1,
                y - neighborhood_size : y + neighborhood_size + 1,
                z - neighborhood_size : z + neighborhood_size + 1,
            ]
            # Get the max value in the neighborhood
            max_value = np.max(neighborhood)
            # If the maximum value is at the voxel we're looking at, this
            # is a maximum and we add the cartesian coordinates and value
            # to our list
            if data_value == max_value:
                x_orig = x - neighborhood_size
                y_orig = y - neighborhood_size
                z_orig = z - neighborhood_size
                maxima_voxel_coord = (x_orig, y_orig, z_orig)
                maxima_vox_coords.append(maxima_voxel_coord)
                maxima_values.append(elf_data[x_orig, y_orig, z_orig])
        maxima_vox_coords = np.array(maxima_vox_coords)
        # convert to fractional coords
        maxima_frac_coords = grid.get_frac_coords_from_vox_full_array(maxima_vox_coords)
        # create a dummy structure and merge nearby maxima
        maxima_structure = grid.structure.copy()
        maxima_structure.remove_species(maxima_structure.symbol_set)
        for frac_coord in maxima_frac_coords:
            maxima_structure.append("He", frac_coord)
        tol = grid.max_voxel_dist * 2
        maxima_structure.merge_sites(tol=tol, mode="average")
        new_maxima_frac_coords = maxima_structure.frac_coords
        # sometimes the pymatgen merge_sites method will return 1 instead of zero
        # for a fractional coordinate. We convert these to 0 here.
        new_maxima_frac_coords = np.where(
            new_maxima_frac_coords == 1, 0, new_maxima_frac_coords
        )
        # maxima_cart_coords = grid.get_cart_coords_from_vox_full_array(maxima_vox_coords)
        return new_maxima_frac_coords  # , maxima_values

    @staticmethod
    def to_number_from_roman_numeral(roman_num: str):
        """
        Converts from a roman numeral to an integer

        Args:
            roman_num (str):
                The roman numeral to convert from

        Returns:
            The integer representation of the roman numeral
        """
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

        Returns:
            A dictionary connecting atomic sites to oxidation states
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
        shannon_radii = []
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
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", category=UserWarning, module="pymatgen"
                )
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
            shannon_radii.append(shannon_radius)
        shannon_radii = np.array(shannon_radii)
        return shannon_radii

    @cached_property
    def elf_radii(self):
        """
        Gets the elf radius of each atom in the structure

        Returns:
            A dictionary connecting atomic sites to their elf ionic radii
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
        partitioning_toolkit = PartitioningToolkit(grid)
        unique_atoms = np.unique(equivalent_atoms)
        unique_atom_radii = {}
        for atom in unique_atoms:
            radius = partitioning_toolkit.get_elf_ionic_radius(
                site_index=atom,
                structure=structure,
            )
            unique_atom_radii[atom] = radius

        # We now construct an array for all of the atoms in the structure
        all_atom_radii = []
        for site_index, site in enumerate(structure):
            equiv_atom = equivalent_atoms[site_index]
            radius = unique_atom_radii[equiv_atom]
            all_atom_radii.append(radius)
        all_atom_radii = np.array(all_atom_radii)

        return all_atom_radii

    def get_ionic_radii(
        self,
        method="elf",
    ):
        """
        Gets the radius for each atom in the structure.

        Args:
            method (str):
                The method used to find the radii. Options are "elf" or "shannon".
                elf will use the provided grid to find the radius of each atom and
                shannon will use bader oxidation states and the closest available
                tabulated shannon crystal radius.

        Returns:
            A dictionary of radii for each atom in the structure.
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
        min_electride_radius: float = 0.6,
        atom_radius_method: str = "elf",
        remove_old_electrides: bool = False,
    ):
        """
        Finds the electrides in a structure using an ELF grid.

        Args:
            electride_finder_cutoff (float):
                The minimum elf value at the site to be considered a possible
                electride. The default is 0.5.
            min_electride_radius (float):
                The minimum elf radius around the maximum for it to be considered
                an electride. The default is 0.6 which is based off of a small
                set of tests.
                An good alternative is 1.19 which is the average radius of fluoride
                in a 6 coordination environment.
            atom_radius_method (str):
                The method used to find the radii. Options are "elf" or "shannon".
                elf will use the provided grid to find the radius of each atom and
                shannon will use bader oxidation states and the closest available
                tabulated shannon crystal radius.
            remove_old_electrides (bool):
                Whether or not to remove any other electrides already placed in
                the system. It is generally recommended that structures without
                electrides are provided.

        Returns:
            A structure object with the found electride sites labeled with "He"
            dummy atoms.
        """
        logging.info("Finding electride sites")
        # Get the coordinates and values of each local maximum in the grid
        grid = self.grid.copy()
        (local_maxima_frac_coords) = self.find_local_maxima(  # , local_maxima_values
            threshold=electride_finder_cutoff
        )
        local_maxima_vox_coords = grid.get_vox_coords_from_frac_full_array(
            local_maxima_frac_coords
        )
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
        electride_coords = []
        # get the estimated shannon radii of each of the sites in the structure.
        # These will be used to estimate electride radii
        radii = self.get_ionic_radii(atom_radius_method)
        for i, maximum_vox_coords in enumerate(local_maxima_vox_coords):
            maximum_frac_coords = local_maxima_frac_coords[i]
            # maximum_cart_coords = local_maxima_cart_coords[i]
            # Create a dummy structure. Add a dummy at the local maximum that
            # was found
            electride_structure = structure.copy()

            electride_structure.append("He", maximum_frac_coords)
            # get all neighbors within 15 A
            (
                site_indices,
                neigh_indices,
                neigh_images,
                dists,
            ) = electride_structure.get_neighbor_list(15)
            # get indices where the electride neighbors are stored
            electride_index = len(electride_structure) - 1
            electride_site_neighs = np.where(site_indices == electride_index)[0]
            # get the subset of indices where the neighbor is not also the electride
            electride_site_neighs = electride_site_neighs[
                neigh_indices[electride_site_neighs] != electride_index
            ]
            # get the distances to these neighbors
            neigh_dists = dists[electride_site_neighs]
            # get the structure indices of these neighbors
            neigh_indices1 = neigh_indices[electride_site_neighs]
            # get the radii for each of these neigbhors
            neigh_radii = radii[neigh_indices1]
            # calculate the maximum radius of the electride relative to each of these
            # neighbors
            max_electride_radii = neigh_dists - neigh_radii
            # check if minimum distance is too close to an atom:
            if min(max_electride_radii) < min_electride_radius:
                continue
            # If the loop is still going, we consider this site an electride. We
            # add it to the list of electride sites.
            electride_coords.append(maximum_frac_coords)

        # Add our potential electride sites to our structure
        electride_structure = structure.copy()
        for coord in electride_coords:
            electride_structure.append("He", coord)

        # report whether any electrides were found
        electride_sites = electride_structure.indices_from_symbol("He")
        if len(electride_sites) > 0:
            logging.info(f"{len(electride_sites)} electride sites found")
        else:
            logging.info("No electride sites found")
        return electride_structure
