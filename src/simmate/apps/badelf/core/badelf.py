# -*- coding: utf-8 -*-

import csv
import itertools
import logging
import math
import warnings
from functools import cached_property
from pathlib import Path

import dask.dataframe
import numpy as np
import pandas as pd
import psutil
from dask.distributed import Client, LocalCluster
from numpy.typing import ArrayLike
from pymatgen.analysis.dimensionality import get_dimensionality_larsen
from pymatgen.analysis.graphs import StructureGraph
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.io.vasp import Potcar

from simmate.apps.badelf.core.electride_finder import ElectrideFinder
from simmate.apps.badelf.core.grid import Grid
from simmate.apps.badelf.core.partitioning import PartitioningToolkit
from simmate.apps.badelf.core.voxel_assignment import VoxelAssignmentToolkit
from simmate.apps.bader.outputs import ACF
from simmate.workflows.utilities import get_workflow

# BUG: we shouldn't fully turning off warnings. This should be used within a context.
warnings.filterwarnings("ignore")


class BadElfToolkit:
    """
    A set of tools for performing BadELF, VoronELF, or Zero-Flux analysis on
    outputs from a VASP calculation.

    Args:
        partitioning_grid (Grid):
            A badelf app Grid like object used for partitioning the unit cell
            volume. Usually contains ELF.
        charge_grid (Grid):
            A badelf app Grid like object used for summing charge. Usually
            contains charge density.
        directory (Path):
            The Path to perform the analysis in.
        cores (int):
            The number of cores (NOT threads) to use for voxel assignment.
            Defaults to 0.9*the total number of cores available.
        algorithm (str):
            The algorithm to use for partitioning. Options are "badelf", "voronelf",
            or "zero-flux".
        find_electrides (bool):
            Whether or not to search for electride sites. Usually set to true.
    """

    check_for_covalency = True
    electride_finder_cutoff = 0.5
    electride_connection_cutoff = 0

    def __init__(
        self,
        partitioning_grid: Grid,
        charge_grid: Grid,
        directory: Path,
        cores: int = None,
        algorithm: str = "badelf",
        find_electrides: bool = True,
    ):
        if partitioning_grid.structure != charge_grid.structure:
            raise ValueError("Grid structures must be the same.")
        if cores is None:
            self.cores = math.floor(len(psutil.Process().cpu_affinity()) * 0.9 / 2)
        else:
            self.cores = cores

        # Check if POTCAR exists in path. If not, throw warning
        if not (directory / "POTCAR").exists():
            raise Exception(
                """
                No POTCAR file found in the requested directory.
                """
            )
        if algorithm not in ["badelf", "voronelf", "zero-flux"]:
            raise ValueError(
                """The algorithm setting you chose does not exist. Please select
                  either 'badelf', 'voronelf', or 'zero-flux'.
                  """
            )

        self.partitioning_grid = partitioning_grid
        self.charge_grid = charge_grid
        self.directory = directory
        self.algorithm = algorithm
        self.find_electrides = find_electrides

        self._single_site_voxel_assignments = None
        self._two_site_voxel_assignments = None
        self._multi_site_voxel_assignments = None
        self.voxel_assignments_array = None

    @cached_property
    def structure(self):
        structure = self.partitioning_grid.structure.copy()
        structure.remove_species(["He"])
        return structure

    @cached_property
    def electride_structure(self):
        """
        Searches the partitioning grid for potential electride sites and returns
        a structure with the found sites.

        Returns:
            A Structure object with electride sites as "He" atoms.
        """

        if self.find_electrides:
            electride_structure = ElectrideFinder(
                self.partitioning_grid,
                self.directory,
            ).get_electride_structure(
                electride_finder_cutoff=self.electride_finder_cutoff
            )
        else:
            electride_structure = self.structure

        return electride_structure

    @cached_property
    def electride_indices(self):
        """
        The indices of the structure that are electride sites.
        """
        return self.electride_structure.indices_from_symbol("He")

    @cached_property
    def coord_envs(self):
        """
        The coordination environment around each electride.
        """
        return self._get_coord_envs()

    def _get_coord_envs(self):
        """
        Gets the coordination environment for electrides in the system.

        Returns:
            A list of coordination environments in order of the electrides in
            the system.
        """
        # create a CrystalNN loop
        cnn = CrystalNN()
        coord_envs = []
        # For each electride in the structure, we make a new temporary structure
        # without electride sites. We then add one electride site at a time and
        # check its environment.
        for i, site in enumerate(self.electride_structure):
            coord_envs.append(cnn.get_cn(structure=self.electride_structure, n=i))
        return coord_envs

    @cached_property
    def partitioning(self):
        """
        The partitioning planes for the structure as a dictionary of dataframes.
        None if the zero-flux method is selected
        """
        return self._get_partitioning()

    def _get_partitioning(self):
        """
        Gets the partitioning used in the badelf and voronelf algorithms.

        Returns:
            Dictionary relating sites to the planes surrounding them. None
            if the zero-flux algorithm is selected.
        """
        # Get the partitioning grid
        partitioning_grid = self.partitioning_grid.copy()
        # partitioning_grid.regrid()
        # If the algorithm is badelf, we don't want to partition with the structure
        # containing electrides. We remove any electrides in case the provided
        # structure already had them.
        if self.algorithm == "badelf":
            # remove electrides from grid structure and get
            partitioning_grid.structure.remove_species("He")
            partitioning = PartitioningToolkit(partitioning_grid).get_partitioning(
                check_for_covalency=self.check_for_covalency
            )
            return partitioning
        elif self.algorithm == "voronelf":
            # Use the structure with electrides as the partitioning structure.
            # This will not be anything different from the base structure if there
            # are no electride sites.
            partitioning_grid.structure = self.electride_structure.copy()
            partitioning = PartitioningToolkit(partitioning_grid).get_partitioning(
                check_for_covalency=self.check_for_covalency
            )
            return partitioning
        elif self.algorithm == "zero-flux":
            print(
                """
                There is no partitioning property for the zero-flux algorithm as
                the partitioning is handled by the [Henkelman Bader code](https://theory.cm.utexas.edu/henkelman/code/bader/)
                """
            )
            return None

    @cached_property
    def voxel_assignments(self):
        """
        A dataframe with each voxel coordinate, charge, and dictionary of sites
        that the voxel is assigned to.
        """
        return self._get_voxel_assignments()

    def _get_voxel_assignments(self):
        """
        Gets a dataframe of voxel assignments. The dataframe has columns
        [x, y, z, charge, sites]
        """
        logging.info("Beginning voxel assignment (this can take a while)")
        algorithm = self.algorithm
        if algorithm == "zero-flux":
            print(
                """
                There is no voxel assignment for the zero-flux algorithm as
                the assignment is handled by the [Henkelman Bader code](https://theory.cm.utexas.edu/henkelman/code/bader/)
                """
            )
            return None

        # Get the objects that we'll need to assign voxels.
        elif algorithm in ["badelf", "voronelf"]:
            charge_grid = self.charge_grid
            voxel_assignment_tools = VoxelAssignmentToolkit(
                charge_grid=charge_grid,
                partitioning=self.partitioning,
                electride_structure=self.electride_structure,
                algorithm=self.algorithm,
                directory=self.directory,
            )
            # get an initial array of no site assignments
            all_voxel_site_assignments = np.zeros(charge_grid.voxel_num)
            if algorithm == "badelf":
                # Get the voxel assignments for each electride site
                all_voxel_site_assignments = self._get_zero_flux_electride_assignment(
                    all_voxel_site_assignments
                )

            # get assignments for voxels belonging to single sites
            single_site_voxel_assignments = (
                voxel_assignment_tools.get_single_site_voxel_assignments(
                    all_voxel_site_assignments
                )
            )
            voxel_assignment_tools = VoxelAssignmentToolkit(
                charge_grid=charge_grid,
                partitioning=self.partitioning,
                electride_structure=self.electride_structure,
                algorithm=self.algorithm,
                directory=self.directory,
            )
            # get assignments for voxels split by two or more sites
            (
                two_site_voxel_assignments,
                multi_site_voxel_assignments,
                voxel_assignments_array,
            ) = voxel_assignment_tools.get_intersected_voxel_volume_ratio(
                single_site_voxel_assignments
            )

            self._single_site_voxel_assignments = single_site_voxel_assignments
            self._two_site_voxel_assignments = two_site_voxel_assignments
            self._multi_site_voxel_assignments = multi_site_voxel_assignments
            self.voxel_assignments_array = voxel_assignments_array

        logging.info("Finished voxel assignment")
        return (
            single_site_voxel_assignments,
            two_site_voxel_assignments,
            multi_site_voxel_assignments,
        )

    def write_electride_structure_files(
        self,
        charge_file: str = "CHGCAR_w_empty_atoms",
        partitioning_file: str = "ELFCAR_w_empty_atoms",
    ):
        """
        Writes copies of the charge file and partitioning file (usually CHGCAR
        and ELFCAR) with electride sites. This is most frequently used for
        eventually running the Henkelman Bader code to get electride charges.
        """
        # Write CHGCAR and ELFCAR files with the empty structure that was found
        electride_charge_grid = self.charge_grid.copy()
        electride_charge_grid.structure = self.electride_structure
        electride_charge_grid.write_file(charge_file)
        electride_elf_grid = self.partitioning_grid.copy()
        # check that elf grid is same size as charge grid and if not, regrid
        if electride_charge_grid.voxel_num != electride_elf_grid.voxel_num:
            electride_elf_grid.regrid(new_grid_shape=electride_charge_grid.grid_shape)
        electride_elf_grid.structure = self.electride_structure
        electride_elf_grid.write_file(partitioning_file)

    def _get_zero_flux_electride_assignment(
        self, all_voxel_site_assignments: ArrayLike
    ):
        """
        Gets the electride site assignments for voxels belonging to electride
        sites based on the Henkelman groups algorithm.

        Args:
            all_voxel_site_assignments (ArrayLike):
                The array to add the voxel assignments to.

        Returns:
            updated voxel_assignments dataframe
        """

        directory = self.directory
        charge_file = directory / "CHGCAR_w_empty_atoms"
        partitioning_file = directory / "ELFCAR_w_empty_atoms"
        if not (directory / "CHGCAR_w_empty_atoms").exists():
            self.write_electride_structure_files(charge_file, partitioning_file)
        # Run the henkelman code to print out electride files
        badelf_workflow = get_workflow("population-analysis.bader.bader-dev")
        badelf_workflow.run(
            directory=directory,
            charge_file="CHGCAR_w_empty_atoms",
            partitioning_file="ELFCAR_w_empty_atoms",
            atoms_to_print=self.electride_indices,
        )
        height, width, depth = self.charge_grid.grid_shape

        for electride in self.electride_indices:
            # Pull in electride charge density from bader output file (BvAt####.dat format)
            self._fix_BvAt(f"BvAt{str(electride+1).zfill(4)}.dat")
            electride_charge = Grid.from_file(
                directory / f"BvAt{str(electride+1).zfill(4)}.dat"
            ).total
            x, y, z = np.where(electride_charge != 0)
            electride_indices_1D = x + y * width + z * width * height
            all_voxel_site_assignments[electride_indices_1D] = electride + 1

        return all_voxel_site_assignments

    def get_electride_dimensionality(self, electride_connection_cutoff: float = 0):
        electride_indices = self.electride_indices
        # If we have no electrides theres no reason to continue so we stop here
        if len(electride_indices) == 0:
            return None

        if self.algorithm == "zero-flux":
            # !!! read in electride only ELFCAR. Regrid to charge_grid size
            # Get the necessary CHGCAR and ELFCAR files. Then run the
            # Henkelman Bader code, printing the resulting electride voxels in
            # one file for topolgoy analysis.
            directory = self.directory
            partitioning_file = directory / "ELFCAR_w_empty_atoms"
            if not partitioning_file.exists():
                self.write_electride_structure_files(
                    directory / "CHGCAR_w_empty_atoms", partitioning_file
                )
            badelf_workflow = get_workflow("population-analysis.bader.bader-dev")
            badelf_workflow.run(
                directory=directory,
                charge_file="ELFCAR_w_empty_atoms",
                partitioning_file="ELFCAR_w_empty_atoms",
                species_to_print="He",
                structure=self.electride_structure,
            )
            self._fix_BvAt("BvAt_summed.dat")
            elf_grid = Grid.from_file(directory / "BvAt_summed.dat")
            elf_grid.regrid(desired_resolution=self.charge_grid.voxel_resolution)
            pass
        elif self.algorithm in ["badelf", "voronelf"]:
            # read in ELF data and regrid so that it is the same size as the
            # charge grid
            elf_grid = self.partitioning_grid.copy()
            elf_grid.regrid(desired_resolution=self.charge_grid.voxel_resolution)
            voxel_assignment_array = self.voxel_assignments_array
            # Get array where values are ELF values when voxels belong to electrides
            # and are 0 otherwise
            elf_array = np.where(
                np.isin(voxel_assignment_array, electride_indices), elf_grid.total, 0
            )
            elf_grid.total = elf_array

        # read in structure and remove all atoms except dummy electride sites
        electride_structure = self.electride_structure.copy()

        electride_structure.remove_species(self.structure.symbol_set)

        elf_grid.structure = electride_structure

        partitioning_tools = PartitioningToolkit(elf_grid)

        # get the 50 nearest electride neighbors. We only do this because we need to make
        # sure that electride sites that are very far away are thoroughly checked
        nearest_neighbors = partitioning_tools.get_set_number_of_neighbors(50)

        # create an empty StructureGraph object. This maps connections between different
        # atoms, including those across unit cell boundaries. We will fill this out using
        # the list of neighbors we just defined.
        graph = StructureGraph.with_empty_graph(electride_structure)
        # partitioning_lines = []
        # iterate over each unique electride site.
        for index, neighbors in enumerate(nearest_neighbors):
            # get the voxel coords for the electride site
            site_pos = elf_grid.get_voxel_coords_from_index(index)

            # loop over the neighboring electride sites
            for neighbor in neighbors:
                # We will have many excess electride sites that are in unit cells that
                # don't border the one we're looking at. I'm not certain, but I don't
                # think those are necessary. We cut them out here to save time from the
                # get_partitioning_line_from_voxels function.

                # Assume this neighbor is not more than one unit cell away
                more_than_1_unit_cell_away = False
                for integer in neighbor.image:
                    # Check if an integer other than -1, 1, or 0 is present. This indicates
                    # we've been transformed more than one unit cell away.
                    if integer not in [-1, 0, 1]:
                        more_than_1_unit_cell_away = True
                        break
                # Check if we've moved more than one unit cell away. If we have, skip
                # to the next neighbor
                if more_than_1_unit_cell_away:
                    continue

                # get the voxel coord for the connected electride site and get the ELF
                # line between the site and this neighbor
                neigh_pos = elf_grid.get_voxel_coords_from_neigh(neighbor)
                pos, values = partitioning_tools.get_partitioning_line_from_voxels(
                    site_pos, neigh_pos
                )
                # partitioning_lines.append([pos,values])
                # If a 0 is not found in the elf line these sites are connected and we
                # want to add an edge to our graph.
                #!!! create cutoff for how much space is allowed between sites
                # for when vorelf cuts it off by a voxel or so?
                if all(value > electride_connection_cutoff for value in values):
                    graph.add_edge(
                        from_index=index,  # The site index of the electride site of interest
                        from_jimage=(
                            0,
                            0,
                            0,
                        ),  # The image the electride site is in. Always (0,0,0)
                        to_index=neighbor.index,  # The neighboring electrides site index
                        to_jimage=neighbor.image,  # The image that the neighbor is in.
                        weight=None,  # The relative weight of the neighbor. We ignore this.
                        edge_properties=None,
                        warn_duplicates=False,  # Duplicates are fine for us.
                    )

        # Get the dimensionality from our StructureGraph. If more than one group of electrides
        # is found, it will default to the highest dimensionality.
        return get_dimensionality_larsen(graph)

    def _fix_BvAt(self, file_name):
        electride_structure = self.electride_structure
        symbols = electride_structure.types_of_species
        new_symbol_line = ""
        for symbol in symbols:
            new_symbol_line += f"{symbol.name}   "
        directory = self.directory
        with open(directory / f"{file_name}", "r") as file:
            content = file.readlines()
        symbol_line = content[5]
        if not all(symbol.name in symbol_line for symbol in symbols):
            content[5] = new_symbol_line + "\n"
            with open(directory / f"{file_name}", "w") as file:
                file.writelines(content)

    @cached_property
    def results(self):
        """
        A summary of the results from a BadELF run.
        """
        return self._get_results()

    def _get_results(self):
        algorithm = self.algorithm
        directory = self.directory
        electride_num = len(self.electride_indices)
        electride_structure = self.electride_structure
        electride_indices = self.electride_indices
        a, b, c = self.charge_grid.grid_shape
        elements = []
        for site in electride_structure:
            if site.species_string == "He":
                elements.append("e")
            else:
                elements.append(site.species_string)

        if algorithm == "zero-flux":
            # Get the necessary CHGCAR and ELFCAR files. Then run the
            # Henkelman Bader code, printing the resulting electride voxels in
            # one file for topolgoy analysis.
            charge_file = directory / "CHGCAR_w_empty_atoms"
            partitioning_file = directory / "ELFCAR_w_empty_atoms"
            self.write_electride_structure_files(charge_file, partitioning_file)
            badelf_workflow = get_workflow("population-analysis.bader.bader-dev")
            badelf_workflow.run(
                directory=directory,
                charge_file="CHGCAR_w_empty_atoms",
                partitioning_file="ELFCAR_w_empty_atoms",
            )
            # get the desired data that will be saved to the dataframe
            #!!! I should rework the ACF.dat reader now that I have better
            # tools than pymatgen's reader
            logging.info("Calculating additional useful information")
            results_dataframe, extra_data = ACF(directory)
            results = {
                "oxidation_states": list(results_dataframe.oxidation_state.values),
                "charges": list(results_dataframe.charge.values),
                "min_dists": list(results_dataframe.min_dist.values),
                "atomic_volumes": list(results_dataframe.atomic_vol.values),
                **extra_data,
            }

        elif algorithm in ["badelf", "voronelf"]:
            # get the voxel assignments. Note that the convention here is to
            # have indices starting at 1 rather than 0
            (
                single_site_assignments,
                two_site_assignments,
                multi_site_assignments,
            ) = self.voxel_assignments
            voxel_volume = self.charge_grid.voxel_volume
            charge_array = self.charge_grid.total.ravel()
            logging.info("Calculating additional useful information")
            # Create dictionaries to store the important results
            min_dists = {}
            charges = {}
            atomic_volumes = {}
            # Get min dists
            for site in range(len(electride_structure)):
                charges[site] = 0
                atomic_volumes[site] = 0
            # Get the minimum distances from each atom the the partitioning
            # surface. If the algorithm is "badelf" we need to acquire the
            # radii for the electrides
            if algorithm == "badelf":
                results_dataframe, extra_data = ACF(directory)
                electride_min_dists = results_dataframe.min_dist
            for site in range(len(electride_structure)):
                # fill min_dist dictionary using the smallest partitioning radius
                if site in electride_indices and algorithm == "badelf":
                    # Get dist from henkelman algorithm results
                    min_dists[site] = electride_min_dists[site]
                else:
                    # Get dists from partitioning
                    radii = []
                    for neighbor_index, row in self.partitioning[site].iterrows():
                        radii.append(row["radius"])
                    min_radii = min(radii)
                    min_dists[site] = min_radii

            # Get the charge and atomic volume of each site for sites with
            # one assignment
            for site in range(len(electride_structure)):
                site1 = site + 1
                voxel_indices = np.where(single_site_assignments == site1)[0]
                site_charge = charge_array[voxel_indices]
                charges[site] += np.sum(site_charge)
                atomic_volumes[site] += len(voxel_indices) * voxel_volume
            # Get the charge and atomic volume of each site with 2 site assignments.
            # these are stored in an array with 5 columns representing the voxel
            # index, the fraction for the first site, thre fraction for the
            # second site, the first site index, and the second site index
            for site in range(len(electride_structure)):
                site1 = site + 1
                first_site_sub_indices = np.where(two_site_assignments[:, 3] == site1)
                second_site_sub_indices = np.where(two_site_assignments[:, 4] == site1)
                first_site_indices = two_site_assignments[:, 0][first_site_sub_indices]
                second_site_indices = two_site_assignments[:, 0][
                    second_site_sub_indices
                ]
                first_site_fracs = two_site_assignments[:, 1][first_site_sub_indices]
                second_site_fracs = two_site_assignments[:, 2][second_site_sub_indices]
                first_site_charges = charge_array[first_site_indices.astype(int)]
                second_site_charges = charge_array[second_site_indices.astype(int)]
                total_charge = np.sum(first_site_fracs * first_site_charges) + np.sum(
                    second_site_fracs * second_site_charges
                )
                total_volume = np.sum(first_site_fracs) + np.sum(second_site_fracs)
                charges[site] += total_charge
                atomic_volumes[site] += total_volume
            # Get the charge and atomic volume of each site with multiple site
            # assignments. These are stored in a dictionary with the keys
            # "indices", "sites", and "fracs"
            for index, sites in enumerate(multi_site_assignments["sites"]):
                voxel_index = multi_site_assignments["indices"][index]
                fracs = multi_site_assignments["fracs"][index]
                voxel_charge = charge_array[voxel_index]
                for site, frac in zip(sites, fracs):
                    charges[site - 1] += voxel_charge * frac
                    atomic_volumes[site - 1] += voxel_volume * frac

            # Convert charges from VASP standard
            for site, charge in charges.items():
                charges[site] = charge / (a * b * c)

            # Get the number of electrons assigned by badelf.
            nelectrons = round(sum(charges.values()), 6)

            # Get
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                potcars = Potcar.from_file(directory / "POTCAR")
            nelectron_data = {}
            # the result is a list because there can be multiple element potcars
            # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
            for potcar in potcars:
                nelectron_data.update({potcar.element: potcar.nelectrons})

            # create lists to store the element list, oxidation states, charges,
            # minimum distances, and atomic volumes
            oxi_state_data = []
            charges_list = []
            min_dists_list = []
            atomic_volumes_list = []
            # iterate over the charge results and add the results to each list
            for site_index, site_charge in charges.items():
                # get structure site
                site = electride_structure[site_index]
                # get element name
                element_str = site.specie.name
                # Change electride dummy atom name to e
                if element_str == "He":
                    element_str = "e"
                # calculate oxidation state and add it to the oxidation state list
                if element_str == "e":
                    oxi_state = -site_charge
                else:
                    oxi_state = nelectron_data[element_str] - site_charge
                oxi_state_data.append(oxi_state)
                # add the corresponding charge, distance, and atomic volume to the
                # respective lits
                charges_list.append(site_charge)
                min_dists_list.append(min_dists[site_index])
                atomic_volumes_list.append(atomic_volumes[site_index])

            # Calculate the "vacuum charge" or the charge not associated with any atom.
            # Idealy this should be 0.
            total_electrons = 0
            for site in self.structure:
                site_valence_electrons = nelectron_data[site.species_string]
                total_electrons += site_valence_electrons
            vacuum_charge = round((total_electrons - nelectrons), 6)

            # Calculate the "vacuum volume" or the volume not associated with any atom.
            # Idealy this should be 0
            vacuum_volume = round(
                (self.structure.volume - sum(atomic_volumes.values())), 6
            )

            # Save everything in a results dictionary
            results = {
                "oxidation_states": oxi_state_data,
                "charges": charges_list,
                "min_dists": min_dists_list,
                "atomic_volumes": atomic_volumes_list,
                "vacuum_charge": vacuum_charge,
                "vacuum_volume": vacuum_volume,
                "nelectrons": nelectrons,
            }

        # set the results that are not algorithm dependent
        results["nelectrides"] = electride_num
        results["algorithm"] = algorithm
        results["element_list"] = elements
        results["coord_envs"] = self.coord_envs
        results["electride_dim"] = self.get_electride_dimensionality(
            electride_connection_cutoff=self.electride_connection_cutoff
        )
        results["elf_connect_cutoff"] = self.electride_connection_cutoff
        # Fill out columns unrelated to badelf alg
        structure = self.structure
        results["structure"] = structure

        return results

    def write_results_csv(self):
        directory = self.directory
        results = self.results
        with open(directory / "badelf_summary.csv", "w") as csv_file:
            writer = csv.writer(csv_file)
            for key, value in results.items():
                writer.writerow([key, value])

    @classmethod
    def from_files(
        cls,
        directory: Path = Path("."),
        partitioning_file: str = "ELFCAR",
        charge_file: str = "CHGCAR",
        algorithm: str = "badelf",
        find_electrides: bool = True,
        cores: int = None,
    ):
        """
        Creates a BadElfToolkit instance from the requested partitioning file
        and charge file.

        Args:
            directory (Path):
                The path to the directory that the badelf analysis
                will be located in.
            partitioning_file (str):
                The filename of the file to use for partitioning. Must be a VASP
                CHGCAR or ELFCAR type file.
            charge_file (str):
                The filename of the file containing the charge information. Must
                be a VASP CHGCAR or ELFCAR type file.
            algorithm (str):
                The algorithm to use. Options are "badelf", "voronelf", or "zero-flux"
            find_electrides (bool):
                Whether or not to search for electrides in the system
            cores (int):
                The number of computer cores (NOT threads) that will be used to
                parallelize
        """

        partitioning_grid = Grid.from_file(directory / partitioning_file)
        charge_grid = Grid.from_file(directory / charge_file)
        return BadElfToolkit(
            partitioning_grid=partitioning_grid,
            charge_grid=charge_grid,
            directory=directory,
            algorithm=algorithm,
            find_electrides=find_electrides,
        )

    def write_species_file(self, file_type: str = "elf", species: str = "He"):
        voxel_assignment_array = self.voxel_assignments_array
        if file_type == "elf":
            grid = self.partitioning_grid.copy()
            grid.regrid(desired_resolution=self.charge_grid.voxel_resolution)
        elif file_type == "charge":
            grid = self.charge_grid.copy()
        else:
            raise ValueError(
                """
                Invalid file_type. Options are "elf" or "charge".
                """
            )
        grid.structure = self.electride_structure
        indices = self.electride_structure.indices_from_symbol(species)
        # Get array where values are ELF values when voxels belong to electrides
        # and are 0 otherwise
        array = np.where(np.isin(voxel_assignment_array, indices), grid.total, 0)
        grid.total = array
        if grid.diff is not None:
            diff_array = np.where(
                np.isin(voxel_assignment_array, indices), grid.diff, 0
            )
            grid.diff = diff_array

        if species == "He":
            species = "e"
        if file_type == "elf":
            grid.write_file(f"ELFCAR_{species}")
        elif file_type == "charge":
            grid.write_file(f"CHGCAR_{species}")

    def write_atom_file(
        self,
        atom_index: int,
        file_type: str = "elf",
    ):
        voxel_assignment_array = self.voxel_assignments_array
        if file_type == "elf":
            grid = self.partitioning_grid.copy()
            grid.regrid(desired_resolution=self.charge_grid.voxel_resolution)
        elif file_type == "charge":
            grid = self.charge_grid.copy()
        else:
            raise ValueError(
                """
                Invalid file_type. Options are "elf" or "charge".
                """
            )
        grid.structure = self.electride_structure
        # Get array where values are ELF values when voxels belong to electrides
        # and are 0 otherwise
        array = np.where(np.isin(voxel_assignment_array, atom_index), grid.total, 0)
        grid.total = array
        if grid.diff is not None:
            diff_array = np.where(
                np.isin(voxel_assignment_array, atom_index), grid.diff, 0
            )
            grid.diff = diff_array

        if file_type == "elf":
            grid.write_file(f"ELFCAR_{atom_index}")
        elif file_type == "charge":
            grid.write_file(f"CHGCAR_{atom_index}")

    def plot_partitioning(self):
        """
        Plots the partitioning surface around each atom.
        """
        partitioning = self.partitioning
        grid = self.partitioning_grid.copy()
        if self.algorithm == "badelf":
            grid.structure = self.structure
            PartitioningToolkit(grid).plot_partitioning_results(partitioning)
        elif self.algorithm == "voronelf":
            grid.structure = self.electride_structure
            PartitioningToolkit(grid).plot_partitioning_results(partitioning)
        else:
            print(
                f"""
                Plotting of zero-flux partitioning surfaces is not currently
                supported.
                """
            )
