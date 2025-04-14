# -*- coding: utf-8 -*-

import csv
import logging
import math
import os
import warnings
from functools import cached_property
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import psutil
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.core import Element
from pymatgen.io.vasp import Potcar
from scipy.ndimage import label
from tqdm import tqdm

from simmate.apps.badelf.core.elf_analyzer import ElfAnalyzerToolkit
from simmate.apps.badelf.core.partitioning import PartitioningToolkit
from simmate.apps.badelf.core.voxel_assignment import VoxelAssignmentToolkit
from simmate.apps.bader.toolkit import Grid
from simmate.toolkit import Structure


class BadElfToolkit:
    """
    A set of tools for performing BadELF, VoronELF, or Zero-Flux analysis on
    outputs from a VASP calculation. This class only performs analysis
    on one spin at a time.

    Args:
        partitioning_grid (Grid):
            A badelf app Grid like object used for partitioning the unit cell
            volume. Usually contains ELF.
        charge_grid (Grid):
            A badelf app Grid like object used for summing charge. Usually
            contains charge density.
        directory (Path):
            The Path to perform the analysis in.
        threads (int):
            The number of threads to use for voxel assignment.
            Defaults to 0.9*the total number of threads available.
        algorithm (str):
            The algorithm to use for partitioning. Options are "badelf", "voronelf",
            or "zero-flux".
        find_electrides (bool):
            Whether or not to search for electride sites. Usually set to true.
        labeled_structure :
            A pymatgen structure object with dummy atoms representing
            electride, covalent, and metallic features
        shared_feature_separation_method (str):
            The method of assigning charge from shared ELF features
            such as covalent or metallic bonds.
        shared_feature_algorithm (str):
            The algorithm used to partition covalent bonds found in the
            structure. Only used for separation methods other than the
            plane method.
        ignore_low_pseudopotentials (bool):
            Whether to ignore warnings about missing atomic basins
            due to using pseudopotentials with a small amount of
            valence electrons.
        downscale_resolution (int):
            The resolution in voxels/Angstrom^3 that the grids should be
            downscaled to in the ElfAnalysisToolkit
        elf_analyzer_kwargs (dict):
            A dictionary of keyword arguments to pass to the ElfAnalyzerToolkit
            class.

    """

    def __init__(
        self,
        partitioning_grid: Grid,
        charge_grid: Grid,
        directory: Path,
        threads: int = None,
        algorithm: Literal["badelf", "voronelf", "zero-flux"] = "badelf",
        shared_feature_separation_method: Literal[
            "plane", "pauling", "equal"
        ] = "pauling",
        shared_feature_algorithm: Literal["zero-flux", "voronoi"] = "zero-flux",
        find_electrides: bool = True,
        labeled_structure: Structure = None,
        ignore_low_pseudopotentials: bool = False,
        downscale_resolution: int = 1200,
        elf_analyzer_kwargs: dict = dict(
            resolution=0.01,
            include_lone_pairs=False,
            include_shared_features=True,
            metal_depth_cutoff=0.1,
            min_covalent_angle=135,
            min_covalent_bond_ratio=0.4,
            shell_depth=0.05,
            electride_elf_min=0.5,
            electride_depth_min=0.2,
            electride_charge_min=0.5,
            electride_volume_min=10,
            electride_radius_min=0.3,
            radius_refine_method="linear",
            write_results=True,
        ),
    ):
        if partitioning_grid.structure != charge_grid.structure:
            raise ValueError("Grid structures must be the same.")
        if threads is None:
            self.threads = math.floor(psutil.Process().num_threads() * 0.9 / 2)
        else:
            self.threads = threads

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
        self.labeled_structure = labeled_structure
        if shared_feature_separation_method == "plane":
            if algorithm == "zero-flux":
                logging.warning(
                    "The `plane` shared feature separation cannot be used with the zero-flux algorithm. Defaulting to pauling method."
                )
                shared_feature_separation_method = "pauling"
            # We don't want to treat shared features as their own entities
            self.shared_feature_algorithm = "none"
        else:
            self.shared_feature_algorithm = shared_feature_algorithm
        if algorithm == "zero-flux" and shared_feature_algorithm == "voronoi":
            logging.warning(
                "The voronoi shared feature algorithm cannot be used with the zero-flux algorithm. Zero-flux will be used instead."
            )
            self.shared_feature_algorithm = "zero-flux"
        self.shared_feature_separation_method = shared_feature_separation_method
        self.ignore_low_pseudopotentials = ignore_low_pseudopotentials
        self.downscale_resolution = downscale_resolution
        self.elf_analyzer_kwargs = elf_analyzer_kwargs

    @cached_property
    def elf_analyzer(self):
        """
        Returns an ElfAnalyzerToolkit object for this BadELF analysis
        """
        elf_analyzer = ElfAnalyzerToolkit(
            elf_grid=self.partitioning_grid.copy(),
            charge_grid=self.charge_grid.copy(),
            directory=self.directory,
            ignore_low_pseudopotentials=self.ignore_low_pseudopotentials,
            downscale_resolution=self.downscale_resolution,
        )
        return elf_analyzer

    @cached_property
    def elf_analyzer_results(self):
        return self.elf_analyzer.get_full_analysis(**self.elf_analyzer_kwargs)

    @cached_property
    def _find_electrides_and_covalent_bonds(self):
        """
        Searches the partitioning grid for potential electride sites and
        covalent/metallic bonds and returns a structure with the found sites.
        Also returns the neighboring atoms for each of the shared bond
        sites.

        Returns:
            A tuple with a Structure object with electride sites as "e",
            covalent bonds as "z", and metal features as "m" or "le"
            , along with the sites connected by any shared bonds.
        """

        if self.find_electrides:
            electride_structure = self.elf_analyzer_results["structure"]
        else:
            if self.labeled_structure is None:
                raise ValueError(
                    "A labeled structure must be provided if find_electrides is False"
                )
            electride_structure = self.labeled_structure.copy()

        shared_feature_atoms = self.elf_analyzer.get_shared_feature_neighbors(
            electride_structure
        )

        return electride_structure, shared_feature_atoms

    @cached_property
    def electride_structure(self) -> Structure:
        """
        Searches the partitioning grid for potential electride sites and returns
        a structure with the found sites.

        Returns:
            A Structure object with electride sites as "X" atoms.
        """

        return self._find_electrides_and_covalent_bonds[0]

    @cached_property
    def structure(self) -> Structure:
        structure = self.electride_structure.copy()
        # remove all non-atomic sites
        for symbol in ["E", "Z", "M", "Le", "Lp"]:
            if symbol in structure.symbol_set:
                structure.remove_species([symbol])
        return structure

    @cached_property
    def shared_feature_atoms(self):
        """
        Searches the partitioning grid for covalent bonds and returns the atoms
        bonded through each covalent bond.
        """
        return self._find_electrides_and_covalent_bonds[1]

    @cached_property
    def electride_indices(self) -> np.array:
        """
        The indices of the structure that are electride sites.
        """
        return np.array(
            list(self.electride_structure.indices_from_symbol("E")), dtype=int
        )

    @cached_property
    def shared_feature_indices(self) -> np.array:
        """
        The indices of the structure that are covalent or metallic bonds.
        """
        indices = []
        for symbol in ["Z", "M", "Le", "Lp"]:
            indices.extend(self.electride_structure.indices_from_symbol(symbol))
        indices = np.array(indices, dtype=int)
        indices.sort()
        return indices

    @cached_property
    def non_atom_indices(self) -> np.array:
        """
        The indices of the structure that are either electrides, covalent bonds,
        or metallic features
        """
        all_non_atoms_indices = np.concatenate(
            [self.electride_indices, self.shared_feature_indices]
        )
        all_non_atoms_indices.sort()
        return all_non_atoms_indices

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
        cnn = CrystalNN(distance_cutoffs=None)
        coord_envs = []
        # For each site in the structure, we add the coordination environment.

        # We first need to replace any dummy atoms with an atom CrystalNN
        # will recognize. We default to H since it is probably the closest in radius
        electride_structure = self.electride_structure.copy()
        for symbol in ["E", "Z", "M", "Le", "Lp"]:
            if symbol in electride_structure.symbol_set:
                electride_structure.replace_species({symbol: "H1-"})
        for i, site in enumerate(electride_structure):
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", category=UserWarning, module="pymatgen"
                )
                coord_envs.append(cnn.get_cn(structure=electride_structure, n=i))
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
        if self.algorithm == "zero-flux":
            print(
                """
                There is no partitioning property for the zero-flux algorithm as
                the partitioning is handled by the [pybader code](https://github.com/adam-kerrigan/pybader)
                """
            )
            return None
        # Get the partitioning grid
        partitioning_grid = self.partitioning_grid.copy()
        # Which sites we include in the plane partitioning depend on both the
        # algorithm and shared_feature_algorithm. We start with the labeled structure
        # and remove sites as needed
        partitioning_structure = self.electride_structure.copy()
        if self.algorithm != "voronelf":
            partitioning_structure.remove_species("E")
        if self.shared_feature_algorithm != "voronoi":
            for symbol in ["Z", "M", "Le", "Lp"]:
                if symbol in partitioning_structure.symbol_set:
                    partitioning_structure.remove_species([symbol])
        # Now get the partitioning with the given structure
        partitioning_grid.structure = partitioning_structure
        partitioning = PartitioningToolkit(
            partitioning_grid, self.pybader
        ).get_partitioning()
        return partitioning

    @cached_property
    def all_atom_elf_radii(self):
        """
        The elf radii for all atoms-neighbor pairs in the structure. Atom neighbor
        pairs are obtained using CrystalNN while the radii are obtained during
        the partitioning process.
        """
        return self._get_all_atom_elf_radii()

    def _get_all_atom_elf_radii(self):
        """
        Gets the elf radii for all atom-neighbor pairs in the structure.
        """
        if self.algorithm == "zero-flux":
            logging.warn(
                "Elf ionic radii are not calculated when using zero-flux partitioning."
            )
            return None
        atom_elf_radii = pd.DataFrame(
            columns=[
                "site_index",
                "neigh_index",
                "radius",
            ]
        )
        for i, site in enumerate(self.structure):
            coordination = self.coord_envs[i]
            neighbors_df = self.partitioning[i]
            for j in range(coordination):
                neigh_index = neighbors_df.iloc[j]["neigh_index"]
                radius = neighbors_df.iloc[j]["radius"]
                atom_elf_radii.loc[len(atom_elf_radii)] = [i, neigh_index, radius]
        return atom_elf_radii

    def write_atom_elf_radii(self, filename: str = "elf_radii.csv"):
        """
        Writes atomic elf radii to a csv.
        """
        if ".csv" not in filename:
            filename += ".csv"
        if self.all_atom_elf_radii is not None:
            self.all_atom_elf_radii.to_csv(self.directory / filename)
        else:
            logging.warn(
                "Elf ionic radii could not be found (likely due to zero-flux partitioning). No radii will be written."
            )

    @property
    def single_site_voxel_assignments(self):
        """
        A 1D array with site assignments for voxels not exactly on a partitioning
        plane
        """
        return self.voxel_assignments[0]

    @property
    def multi_site_voxel_assignments(self):
        """
        An (N,M) shaped array with indices i,j where i is the voxel index
        (these are sub indices, full indices are stored in multi_site_voxel_indices)
        and j is the site. A 1 indicates that this voxel is partially shared by
        this site
        """
        return self.voxel_assignments[1]

    @property
    def multi_site_voxel_indices(self):
        """
        The corresponding voxel indices for the multi_site_voxel_assignments
        array.
        """
        return np.where(self.single_site_voxel_assignments == 0)[0]

    @cached_property
    def voxel_assignments_array(self):
        """
        A 3D array with the same shape as the charge grid indicating where
        voxels are assigned
        """
        # Get multi site indices
        split_voxel_indices = self.multi_site_voxel_indices
        # create a list to store the randomly assigned voxels
        random_voxel_assignments = []
        # loop through the voxels belonging to multiple sites to pick one random
        # site to assign to.
        for split_voxel in self.multi_site_voxel_assignments:
            # round the assignments
            split_voxel = np.round(split_voxel, 2)
            if len(np.unique(split_voxel)) == 2:
                # There are several sites that share an equal part of this voxel.
                # We want to randomly assign to one of these
                # Get which sites this voxel is split by
                possible_sites = np.where(split_voxel != 0)[0]
                # Pick one randomly
                # site_choice = np.random.choice(possible_sites)
                # !!! For the purposes of electride dimensionality it is better to
                # assign shared voxels to electrides which always have higher index
                # values.
                # !!! With new assignment method it may be better to assign to
                # highest frac or random
                site_choice = possible_sites.max()
                # append it to our list
                random_voxel_assignments.append(site_choice)
            else:
                # There are multiple ratios. We want to assign to the site with
                # the most
                site_choice = np.where(split_voxel == np.max(split_voxel))[0][0]
                random_voxel_assignments.append(site_choice)
        # Get the single site assignments and subtract one to get to sites
        # beginning at 0
        all_site_assignments = self.single_site_voxel_assignments.copy() - 1
        # Assign our randomly generated sites then return the array as a 3D grid
        all_site_assignments[split_voxel_indices] = np.array(random_voxel_assignments)
        return all_site_assignments.reshape(self.charge_grid.shape)

    @cached_property
    def pybader(self):
        """
        A pybader Bader object run on the PartitioningGrid
        """
        bader_grid = self.partitioning_grid.copy()
        bader_grid.structure = self.electride_structure.copy()
        bader = bader_grid.run_pybader(threads=self.threads)
        return bader

    @cached_property
    def zero_flux_voxel_assignments(self):
        """
        An array of the same size as the partitioning grid representing the site
        assignments from the zero-flux partitioning method. This uses the
        [pybader code](https://github.com/adam-kerrigan/pybader)
        """
        return self.pybader.atoms_volumes.copy()

    @cached_property
    def voxel_assignments(self):
        """
        Two arrays representing voxels assigned to only one site and voxels
        assigned to multiple sites
        """
        return self._get_voxel_assignments()

    def _get_voxel_assignments(self):
        """
        Gets a dataframe of voxel assignments. The dataframe has columns
        [x, y, z, charge, sites]
        """
        logging.info("Beginning voxel assignment (this can take a while)")
        algorithm = self.algorithm
        # Get the zero-flux voxel assignments
        all_voxel_site_assignments = self.zero_flux_voxel_assignments.ravel()
        # shift voxel assignments to convention where 0 is unassigned
        all_voxel_site_assignments += 1
        if algorithm == "zero-flux":
            single_site_voxel_assignments = all_voxel_site_assignments
            multi_site_voxel_assignments = np.array([])

        # Get the objects that we'll need to assign voxels.
        elif algorithm in ["badelf", "voronelf"]:
            charge_grid = self.charge_grid
            charge_grid.structure = self.structure
            partitioning = self.partitioning
            voxel_assignment_tools = VoxelAssignmentToolkit(
                charge_grid=charge_grid,
                electride_structure=self.electride_structure.copy(),
                partitioning=partitioning,
                algorithm=self.algorithm,
                directory=self.directory,
                shared_feature_algorithm=self.shared_feature_algorithm,
            )
            initial_voxel_site_assignments = np.zeros(charge_grid.voxel_num)
            if algorithm == "badelf":
                # Get the voxel assignments for each electride or covalent site
                initial_voxel_site_assignments = np.where(
                    np.isin(all_voxel_site_assignments, self.electride_indices + 1),
                    all_voxel_site_assignments,
                    initial_voxel_site_assignments,
                )
            if self.shared_feature_algorithm == "zero-flux":
                # Get voxel assignments for shared features
                initial_voxel_site_assignments = np.where(
                    np.isin(
                        all_voxel_site_assignments, self.shared_feature_indices + 1
                    ),
                    all_voxel_site_assignments,
                    initial_voxel_site_assignments,
                )

            # get assignments for voxels belonging to single sites
            single_site_voxel_assignments = (
                voxel_assignment_tools.get_single_site_voxel_assignments(
                    initial_voxel_site_assignments
                )
            )
            # get assignments for voxels split by two or more sites
            multi_site_voxel_assignments = (
                voxel_assignment_tools.get_multi_site_voxel_assignments(
                    single_site_voxel_assignments.copy()
                )
            )

        logging.info("Finished voxel assignment")
        return (
            single_site_voxel_assignments,
            multi_site_voxel_assignments,
        )

    def get_ELF_maxima(self):
        """
        Gets the ELF maxima at each atom center or bare electron site
        """
        frac_coords = self.electride_structure.frac_coords
        return self.partitioning_grid.interpolate_value_at_frac_coords(
            frac_coords, "cubic"
        )

    @staticmethod
    def get_ELF_dimensionality(grid: Grid, cutoff: float):
        """
        This algorithm works by checking if the voxels with values above the cutoff
        are connected to the equivalent voxel in the unit cell one transformation
        over. This is done primarily using scipy.ndimage.label which determines
        which voxels are connected. To do this rigorously, the unit cell is repeated
        to make a (2,2,2) super cell and the connections are checked going from
        the original unit cell to the unit cells connected at the faces, edges,
        and corners. If a connection in that direction is found, the total number
        of connections increases. Dimensionalities of 0,1,2, and 3 are represented
        by 0,1,4,and 13 connections respectively.

        Args:
            cutoff (float):
                The minimum elf value to consider as a connection.
            grid (Grid):
                The ELF Grid object with only values associated with electrides.
        """
        data = grid.total
        voxel_indices = np.indices(grid.shape).reshape(3, -1).T
        # Remove data below our cutoff
        thresholded_data = np.where(data <= cutoff, 0, 1)
        raveled_data = thresholded_data.ravel()
        # Label connected components in the eroded data. We will check each distinct
        # body to see if it connects in each direction
        structure = np.ones([3, 3, 3])
        labels, num_features = label(thresholded_data, structure=structure)
        if num_features == 0:
            return 0
        # We need to get one voxel in each of the features that we can transpose
        # later on
        feature_indices = []
        for i, site in enumerate(grid.structure):
            if site.species_string == "X":
                frac_coords = site.frac_coords
                voxel_coords = grid.get_voxel_coords_from_frac(frac_coords).astype(int)
                # Make sure that the label is not 0
                site_label = labels[voxel_coords[0], voxel_coords[1], voxel_coords[2]]
                if site_label != 0:
                    feature_indices.append(voxel_coords)
        if len(feature_indices) == 0:
            return 0

        # We are going to need to translate the above voxels and the entire unit
        # cell so we create a list of desired transformations
        transformations = [
            [0, 0, 0],  # -
            [1, 0, 0],  # x
            [0, 1, 0],  # y
            [0, 0, 1],  # z
            [1, 1, 0],  # xy
            [1, 0, 1],  # xz
            [0, 1, 1],  # yz
            [1, 1, 1],  # xyz
        ]
        transformations = np.array(transformations)
        transformations = grid.get_voxel_coords_from_frac(transformations.T).T
        # create a new numpy array representing the data tiled once in each direction
        # to get a corner
        supercell_data = np.zeros(np.array(thresholded_data.shape) * 2)
        for transformation in transformations:
            transformed_indices = (voxel_indices + transformation).astype(int)
            x = transformed_indices[:, 0]
            y = transformed_indices[:, 1]
            z = transformed_indices[:, 2]
            supercell_data[x, y, z] = raveled_data
        # convert data into labeled features
        supercell_data, _ = label(supercell_data, structure)
        # The unit cell can be connected to neighboring unit cells in 26 directions.
        # however, we only need to consider half of these as the others are symmetrical.
        connections = [
            # surfaces (3)
            [0, 1],  # x
            [0, 2],  # y
            [0, 3],  # z
            # edges (6)
            [0, 4],  # xy
            [0, 5],  # xz
            [0, 6],  # yz
            [3, 1],  # x-z
            [3, 2],  # y-z
            [1, 2],  # -xy
            # corners (4)
            [0, 7],  # x,y,z
            [1, 6],  # -x,y,z
            [2, 5],  # x,-y,z
            [3, 4],  # x,y,-z
        ]
        # Using these connections we can determine the dimensionality of the system.
        # 1 connection is 1D, 2-4 connections is 2D and 5-13 connections is 3D.
        # !!! These may need to be updated if I'm wrong. The idea comes from
        # the fact that the connections should be 1, 4, and 13, but sometimes
        # voxelation issues result in a connection not working in one direction
        # while it would in the reverse direction (which isn't possible with
        # true symmetry). The range accounts for this possibility. The problem
        # might be if its possible to have for example a 2D connecting structure
        # with 5 connections. However, I'm pretty sure that immediately causes
        # an increase to 3D dimensionality.
        # First we create a list to store potential dimensionalites based off of
        # each feature. We will take the highest dimensionality.
        dimensionalities = []
        for coord in feature_indices:
            # create count for the number of connections
            connections_num = 0
            for connection in connections:
                # Get voxel coordinates at the first transformation
                x, y, z = (coord + transformations[connection[0]]).astype(int)
                # get voxel coordinates at the second transformation
                x1, y1, z1 = (coord + transformations[connection[1]]).astype(int)
                # get the feature label at each voxel
                label1 = supercell_data[x, y, z]
                label2 = supercell_data[x1, y1, z1]
                # If the labels are the same, the unit cell is connected in this
                # direction
                if label1 == label2:
                    connections_num += 1
            if connections_num == 0:
                dimensionalities.append(0)
            elif connections_num == 1:
                dimensionalities.append(1)
            elif 1 < connections_num <= 4:
                dimensionalities.append(2)
            elif 5 < connections_num <= 13:
                dimensionalities.append(3)

        return max(dimensionalities)

    def get_electride_dimensionality(self):
        """
        Finds the dimensionality (e.g. 0D, 1D, etc.) of an electride by labeling
        features in the ELF at various cutoffs and determining if they are
        connected to nearby unit cells.

        Args:
            grid (Grid):
                The ELF Grid object with only values associated with electrides.
        """
        electride_indices = self.electride_indices
        # If we have no electrides theres no reason to continue so we stop here
        if len(electride_indices) == 0:
            return None, None

        ###############################################################################
        # This section preps an ELF grid that only contains values from the electride
        # sites and is zero everywhere else.
        ###############################################################################

        # read in ELF data and regrid so that it is the same size as the
        # charge grid
        elf_grid = self.partitioning_grid.copy()
        # elf_grid = elf_grid.regrid(desired_resolution=self.charge_grid.voxel_resolution)
        voxel_assignment_array = self.voxel_assignments_array
        # Get array where values are ELF values when voxels belong to electrides
        # and are 0 otherwise
        elf_array = np.where(
            np.isin(voxel_assignment_array, electride_indices), elf_grid.total, 0
        )
        elf_grid.total = elf_array
        elf_grid.structure = self.electride_structure.copy()

        #######################################################################
        # This section scans across different cutoffs to determine what dimensionalities
        # exist in the electride ELF
        #######################################################################
        logging.info("Finding dimensionality cutoffs")
        logging.info("Calculating dimensionality at 0 ELF")
        highest_dimension = self.get_ELF_dimensionality(elf_grid, 0)
        dimensions = [i for i in range(0, highest_dimension)]
        dimensions.reverse()
        # Create lists for the refined dimensions
        final_dimensions = [highest_dimension]
        final_connections = [0]
        amounts_to_change = []
        # We refine by guessing the cutoff is 0.5 then increasing or decreasing by
        # 0.25, then 0.125 etc. down to 0.000015259.
        for i in range(1, 16):
            amounts_to_change.append(1 / (2 ** (i + 1)))
        for dimension in dimensions:
            guess = 0.5
            # assume this dimension is not found
            found_dimension = False
            logging.info(f"Refining cutoff for dimension {dimension}")
            for i in tqdm(amounts_to_change, total=len(amounts_to_change)):
                # check what our current dimension is. If we are at a higher dimension
                # we need to raise the cutoff. If we are at a lower dimension or at
                # the dimension we need to lower it
                current_dimension = self.get_ELF_dimensionality(elf_grid, guess)
                if current_dimension > dimension:
                    guess += i
                elif current_dimension < dimension:
                    guess -= i
                elif current_dimension == dimension:
                    # We have found the dimension so we add it to our lists.
                    guess -= i
                    found_dimension = True
            if found_dimension:
                final_connections.append(round(guess, 4))
                final_dimensions.append(dimension)
        return final_dimensions, final_connections

    @cached_property
    def results(self):
        """
        A summary of the results from a BadELF run.
        """
        return self._get_results()

    def _get_results(self):
        """
        Gets the results for a BadELF run and prints them to a .csv file.
        """
        #######################################################################
        # Get the initial voxel assignments
        #######################################################################
        single_site_assignments, multi_site_assignments = self.voxel_assignments
        logging.info("Calculating additional useful information")
        results = {}
        #######################################################################
        # Algorithm Information
        #######################################################################
        results["algorithm"] = self.algorithm
        results["shared_feature_algorithm"] = self.shared_feature_algorithm
        results["shared_feature_separation_method"] = (
            self.shared_feature_separation_method
        )

        #######################################################################
        # Structure Information
        #######################################################################
        results["structure"] = self.structure
        results["labeled_structure"] = self.electride_structure.copy()
        results["nelectrides"] = len(self.electride_indices)
        results["nshared_features"] = len(self.shared_feature_indices)
        shared_feature_types = []
        for site_idx in self.shared_feature_indices:
            site = self.electride_structure[site_idx]
            shared_feature_types.append(site.specie.symbol)
        results["shared_feature_types"] = shared_feature_types
        results["atom_coord_envs"] = [
            self.coord_envs[i] for i, _ in enumerate(self.structure)
        ]
        results["electride_coord_envs"] = [
            self.coord_envs[i] for i in self.electride_indices
        ]
        results["shared_feature_coord_envs"] = [
            self.coord_envs[i] for i in self.shared_feature_indices
        ]
        results["shared_feature_atoms"] = self.shared_feature_atoms

        #######################################################################
        # ELF Information
        #######################################################################
        results["bifurcation_graph"] = self.elf_analyzer_results["graph"]
        elf_maxima = self.get_ELF_maxima()
        results["atom_elf_maxima"] = [
            elf_maxima[i] for i, _ in enumerate(self.structure)
        ]
        results["electride_elf_maxima"] = [
            elf_maxima[i] for i in self.electride_indices
        ]
        results["shared_feature_elf_maxima"] = [
            elf_maxima[i] for i in self.shared_feature_indices
        ]
        electride_dim, dim_cutoffs = self.get_electride_dimensionality()
        results["electride_dim"] = electride_dim
        results["electride_dim_cutoffs"] = dim_cutoffs

        #######################################################################
        # Charge and Volume Information
        #######################################################################
        # This section requires workup of the information collected through the
        # algorithm
        voxel_volume = self.charge_grid.voxel_volume
        charge_array = self.charge_grid.total.ravel()
        a, b, c = self.charge_grid.shape
        bader = self.pybader

        # First, calculate the charges, volumes, and min dist for each atom, electride
        # and shared feature
        atom_min_dists = {}
        atom_charges = {}
        atom_volumes = {}
        electride_min_dists = {}
        electride_charges = {}
        electride_volumes = {}
        shared_feature_min_dists = {}
        shared_feature_charges = {}
        shared_feature_volumes = {}

        # Get min dists
        def get_voronoi_radius(idx):
            radii = []
            partitioning = self.partitioning
            for neighbor_index, row in partitioning[site].iterrows():
                radii.append(row["radius"])
            min_radii = min(radii)
            return min_radii

        for site in range(len(self.electride_structure)):
            if site in range(len(self.structure)):  # site is atomic
                if self.algorithm == "zero-flux":
                    atom_min_dists[site] = bader.atoms_surface_distance[site]
                else:
                    atom_min_dists[site] = get_voronoi_radius(site)
            elif site in self.electride_indices:  # site is an electride
                if self.algorithm == "voronelf":
                    electride_min_dists[site] = get_voronoi_radius(site)
                else:
                    electride_min_dists[site] = bader.atoms_surface_distance[site]
            elif site in self.shared_feature_indices:
                if (
                    self.shared_feature_algorithm == "voronoi"
                    and self.algorithm != "zero-flux"
                ):
                    shared_feature_min_dists[site] = get_voronoi_radius(site)
                elif self.shared_feature_algorithm == "none":
                    shared_feature_min_dists[site] = 0
                else:
                    if self.shared_feature_algorithm == "voronoi":
                        logging.warn(
                            "The voronoi shared feature algorithm cannot be used with the general zero-flux algorithm"
                        )
                    shared_feature_min_dists[site] = bader.atoms_surface_distance[site]
        # Get charges and volumes from base assignment
        for site in range(len(self.electride_structure)):
            site1 = site + 1
            voxel_indices = np.where(single_site_assignments == site1)[0]
            site_charge = charge_array[voxel_indices]
            if site in range(len(self.structure)):
                atom_charges[site] = np.sum(site_charge)
                atom_volumes[site] = len(voxel_indices) * voxel_volume
            elif site in self.electride_indices:
                electride_charges[site] = np.sum(site_charge)
                electride_volumes[site] = len(voxel_indices) * voxel_volume
            elif site in self.shared_feature_indices:
                shared_feature_charges[site] = np.sum(site_charge)
                shared_feature_volumes[site] = len(voxel_indices) * voxel_volume

        # Get the charge and atomic volume of each voxel with multiple site
        # assignments. These are stored as a (N,M) shaped array where N
        # is the number of split voxels and M is the number of atoms.
        if len(self.multi_site_voxel_assignments) > 0:
            split_voxel_indices = self.multi_site_voxel_indices
            split_voxel_charge = charge_array[split_voxel_indices]
            # get how many sites each voxel is split by
            # split_voxel_ratio = 1 / np.sum(multi_site_assignments, axis=1)
            for site_index, assignment_array in enumerate(multi_site_assignments.T):
                indices_where_assigned = np.where(assignment_array > 0)[0]
                site_charge = split_voxel_charge[indices_where_assigned]
                site_charge = site_charge * assignment_array[indices_where_assigned]
                if site_index in range(len(self.structure)):
                    atom_charges[site_index] += np.sum(site_charge)
                    atom_volumes[site_index] += np.sum(
                        assignment_array[indices_where_assigned] * voxel_volume
                    )
                elif site_index in self.electride_indices:
                    electride_charges[site_index] += np.sum(site_charge)
                    electride_volumes[site_index] += np.sum(
                        assignment_array[indices_where_assigned] * voxel_volume
                    )
                elif site_index in self.shared_feature_indices:
                    shared_feature_charges[site_index] += np.sum(site_charge)
                    shared_feature_volumes[site_index] += np.sum(
                        assignment_array[indices_where_assigned] * voxel_volume
                    )

        # Convert charges from VASP standard and get total electron number
        nelectrons = 0
        for charges in [atom_charges, electride_charges, shared_feature_charges]:
            for site, charge in charges.items():
                new_charge = round((charge / (a * b * c)), 4)
                charges[site] = new_charge
                nelectrons += new_charge
        for volumes in [atom_volumes, electride_volumes, shared_feature_volumes]:
            for site, volume in volumes.items():
                volumes[site] = round(volume, 4)
        results["nelectrons"] = nelectrons

        results["atom_min_dists"] = [i for i in atom_min_dists.values()]
        results["atom_charges"] = [i for i in atom_charges.values()]
        results["atom_volumes"] = [i for i in atom_volumes.values()]
        results["electride_min_dists"] = [i for i in electride_min_dists.values()]
        results["electride_charges"] = [i for i in electride_charges.values()]
        results["electride_volumes"] = [i for i in electride_volumes.values()]
        results["shared_feature_min_dists"] = [
            i for i in shared_feature_min_dists.values()
        ]
        results["shared_feature_charges"] = [i for i in shared_feature_charges.values()]
        results["shared_feature_volumes"] = [i for i in shared_feature_volumes.values()]

        # Calculate oxidation states
        results["electride_oxidation_states"] = [
            -i for i in results["electride_charges"]
        ]
        adjusted_atom_charges = atom_charges.copy()
        for site, charge in enumerate(shared_feature_charges.values()):
            atoms = self.shared_feature_atoms[site]
            if self.shared_feature_separation_method == "equal":
                # The charge should be shared equally between all atoms
                charge_section = charge / len(atoms)
                for neigh_idx in atoms:
                    adjusted_atom_charges[neigh_idx] += charge_section
            elif self.shared_feature_separation_method == "pauling":
                # We want to separate charge based on pauling electronegativity
                # First, we get the electronegativities of each species. We note
                # that the electride electrons do not have electronegativities.
                # We have chosen to use the EN of hydrogen in these cases
                ens = []
                for neigh_idx in atoms:
                    species = self.electride_structure[neigh_idx].specie.symbol
                    if species == "E":
                        ens.append(2.2)
                    else:
                        element = Element(species)
                        en = element.X
                        # If there is no recorded electronegativity, this will
                        # be nan. In this case, we assume an EN of 2.2, though
                        # this is by no means correct
                        if math.isnan(en):
                            en = 2.2
                        ens.append(en)
                # Now we convert the electronegativites to a fraction for each
                # atom. The larger the EN, the more charge the atom will recieve
                ens = np.array(ens)
                ens /= ens.sum()
                for neigh_idx, en_frac in zip(atoms, ens):
                    charge_section = charge * en_frac
                    adjusted_atom_charges[neigh_idx] += charge_section
            else:
                # The plane separation method splits charge during the base of
                # the algorithm, so we just do nothing
                pass

        # Now we calculate oxidation states using data from the POTCAR
        # !!! This prevents us from running BadELF on results other than VASP.
        # Is there another way to guess/get the PPs without the POTCAR?
        # Get POTCAR data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            potcars = Potcar.from_file(self.directory / "POTCAR")
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data.update({potcar.element: potcar.nelectrons})

        atom_oxidation_states = []
        for site_index, site_charge in adjusted_atom_charges.items():
            # get structure site
            site = self.structure[site_index]
            # get element name
            element_str = site.specie.symbol
            if element_str in ["E", "Le", "Z", "Lp", "M"]:
                continue
            # calculate the oxidation state
            oxi_state = round((nelectron_data[element_str] - site_charge), 4)
            atom_oxidation_states.append(oxi_state)

        results["atom_oxidation_states"] = atom_oxidation_states

        # calculate electrides per formula
        # calculate the number of electride electrons per formula unit
        if len(self.electride_indices) > 0:
            electrides_per_unit = sum(
                [electride_charges[i] for i in self.electride_indices]
            )
            (
                _,
                formula_reduction_factor,
            ) = self.structure.composition.get_reduced_composition_and_factor()
            electrides_per_reduced_unit = electrides_per_unit / formula_reduction_factor
            results["electrides_per_formula"] = electrides_per_unit
            results["electrides_per_reduced_formula"] = electrides_per_reduced_unit

        #######################################################################
        # Vacuum Information
        #######################################################################
        total_electrons = 0
        for site in self.electride_structure:
            if site.specie.symbol not in ["E", "Z", "M", "Le", "Lp"]:
                site_valence_electrons = nelectron_data[site.specie.symbol]
                total_electrons += site_valence_electrons
        results["vacuum_charge"] = round((total_electrons - nelectrons), 4)

        # Calculate the "vacuum volume" or the volume not associated with any atom.
        # Idealy this should be 0
        total_volume = 0
        for volumes in [atom_volumes, electride_volumes, shared_feature_volumes]:
            for volume in volumes.values():
                total_volume += volume
        results["vacuum_volume"] = round(self.structure.volume - total_volume, 4)

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
        algorithm: Literal["badelf", "voronelf", "zero-flux"] = "badelf",
        find_electrides: bool = True,
        threads: int = None,
        shared_feature_separation_method: Literal[
            "plane", "pauling", "equal"
        ] = "pauling",
        shared_feature_algorithm: Literal["zero-flux", "voronoi"] = "zero-flux",
        ignore_low_pseudopotentials: bool = False,
        downscale_resolution: int = 1200,
        elf_analyzer_kwargs: dict = dict(
            resolution=0.01,
            include_lone_pairs=False,
            metal_depth_cutoff=0.1,
            min_covalent_angle=135,
            min_covalent_bond_ratio=0.4,
            shell_depth=0.05,
            electride_elf_min=0.5,
            electride_depth_min=0.2,
            electride_charge_min=0.5,
            electride_volume_min=10,
            electride_radius_min=0.3,
            radius_refine_method="linear",
            write_results=True,
        ),
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
            thread (int):
                The number of threads to use for analysis
            shared_feature_separation_method (str):
                The method of assigning charge from shared ELF features
                such as covalent or metallic bonds.
            shared_feature_algorithm (str):
                The algorithm to use for calculating charge on covalent
                and metallic bonds. Options are "zero-flux" or "voronoi"
            ignore_low_pseudopotentials (bool):
                Whether to ignore warnings about missing atomic basins
                due to using pseudopotentials with a small amount of
                valence electrons.
            downscale_resolution (int):
                The resolution in voxels/Angstrom^3 that the grids should be
                downscaled to in the ElfAnalysisToolkit
            elf_analyzer_kwargs (dict):
                A dictionary of keyword arguments to pass to the ElfAnalyzerToolkit
                class.

        Returns:
            A BadElfToolkit instance.
        """

        partitioning_grid = Grid.from_file(directory / partitioning_file)
        charge_grid = Grid.from_file(directory / charge_file)
        return BadElfToolkit(
            partitioning_grid=partitioning_grid,
            charge_grid=charge_grid,
            directory=directory,
            algorithm=algorithm,
            find_electrides=find_electrides,
            threads=threads,
            shared_feature_separation_method=shared_feature_separation_method,
            shared_feature_algorithm=shared_feature_algorithm,
            ignore_low_pseudopotentials=ignore_low_pseudopotentials,
            elf_analyzer_kwargs=elf_analyzer_kwargs,
            downscale_resolution=downscale_resolution,
        )

    def write_species_file(self, file_type: str = "ELFCAR", species: str = "E"):
        """
        Writes an ELFCAR or CHGCAR for a given species. Writes to the default
        directory provided to the BadelfToolkit class.

        Args:
            file_type (str):
                The type of file that you want, either ELFCAR or CHGCAR
            species (str):
                The species to write data for.

        Returns:
            None
        """
        # Get directory
        directory = self.directory
        # Get voxel assignments and data
        voxel_assignment_array = self.voxel_assignments_array
        if file_type == "ELFCAR":
            grid = self.partitioning_grid.copy()
            # grid = grid.regrid(desired_resolution=self.charge_grid.voxel_resolution)
        elif file_type == "CHGCAR":
            grid = self.charge_grid.copy()
        else:
            raise ValueError(
                """
                Invalid file_type. Options are "ELFCAR" or "CHGCAR".
                """
            )
        grid.structure = self.electride_structure
        indices = self.electride_structure.indices_from_symbol(species)
        # Get array where values are ELF values when voxels belong to electrides
        # and are 0 otherwise
        array = np.where(np.isin(voxel_assignment_array, indices), grid.total, 0)
        grid.total = array
        try:
            if grid.diff is not None:
                diff_array = np.where(
                    np.isin(voxel_assignment_array, indices), grid.diff, 0
                )
                grid.diff = diff_array
        except:
            pass

        if species == "X":
            species = "e"
        if file_type == "ELFCAR":
            grid.write_file(directory / f"ELFCAR_{species}")
        elif file_type == "CHGCAR":
            grid.write_file(directory / f"CHGCAR_{species}")

    def write_atom_file(
        self,
        atom_index: int,
        file_type: str = "ELFCAR",
    ):
        """
        Writes an ELFCAR or CHGCAR for a given atom. Writes to the default
        directory provided to the BadelfToolkit class.

        Args:
            file_type (str):
                The type of file that you want, either ELFCAR or CHGCAR
            atom_index (str):
                The index of the atom to write data for.

        Returns:
            None
        """
        # Get directory
        directory = self.directory
        # Get voxel assignments and data
        voxel_assignment_array = self.voxel_assignments_array
        if file_type == "ELFCAR":
            grid = self.partitioning_grid.copy()
        elif file_type == "CHGCAR":
            grid = self.charge_grid.copy()
        else:
            raise ValueError(
                """
                Invalid file_type. Options are "ELFCAR" or "CHGCAR".
                """
            )
        grid.structure = self.electride_structure
        # Get array where values are ELF values when voxels belong to electrides
        # and are 0 otherwise
        array = np.where(np.isin(voxel_assignment_array, atom_index), grid.total, 0)
        grid.total = array
        try:
            if grid.diff is not None:
                diff_array = np.where(
                    np.isin(voxel_assignment_array, atom_index), grid.diff, 0
                )
                grid.diff = diff_array
        except:
            pass

        if file_type == "ELFCAR":
            grid.write_file(directory / f"ELFCAR_{atom_index}")
        elif file_type == "CHGCAR":
            grid.write_file(directory / f"CHGCAR_{atom_index}")

    def write_labeled_structure(self, file_name: str = None, file_type: str = "cif"):
        """
        Writes the structure labeled with the ELF features to file.

        Args:
            file_name (str):
                The base name to use for the file. The reduced formula
                will be used if not provided
            file_type (str):
                The type of file that you want. Allowed types are those
                allowed by pymatgen (e.g. POSCAR, cif)

        Returns:
            None
        """
        if file_name is None:
            file_name = self.partitioning_grid.structure.composition.reduced_formula
        self.electride_structure.to(f"{file_name}_labeled", "cif")

    def plot_partitioning(self):
        """
        Plots the partitioning surface around each atom.
        """
        partitioning, _ = self.partitioning
        grid = self.partitioning_grid.copy()
        if self.algorithm == "badelf":
            grid.structure = self.structure
            PartitioningToolkit(grid, self.pybader).plot_partitioning_results(
                partitioning
            )
        elif self.algorithm == "voronelf":
            grid.structure = self.electride_structure
            PartitioningToolkit(grid, self.pybader).plot_partitioning_results(
                partitioning
            )
        else:
            warnings.warn(
                """
                Plotting of zero-flux partitioning surfaces is not currently
                supported.
                """
            )


class SpinBadElfToolkit:
    """
    This class is a wrapper for the BadElfToolkit adding the capability
    to individually handle spin-up and spin-down components of the
    ELF and charge density.
    """

    def __init__(
        self,
        partitioning_grid: Grid,
        charge_grid: Grid,
        directory: Path = Path("."),
        partitioning_file: str = "ELFCAR",
        charge_file: str = "CHGCAR",
        separate_spin: bool = True,
        algorithm: Literal["badelf", "voronelf", "zero-flux"] = "badelf",
        find_electrides: bool = True,
        labeled_structure_up: Structure = None,
        labeled_structure_down: Structure = None,
        threads: int = None,
        shared_feature_separation_method: Literal[
            "plane", "pauling", "equal"
        ] = "pauling",
        shared_feature_algorithm: Literal["zero-flux", "voronoi"] = "zero-flux",
        ignore_low_pseudopotentials: bool = False,
        downscale_resolution: int = 1200,
        elf_analyzer_kwargs: dict = dict(
            resolution=0.01,
            include_lone_pairs=False,
            metal_depth_cutoff=0.1,
            min_covalent_angle=135,
            min_covalent_bond_ratio=0.4,
            shell_depth=0.05,
            electride_elf_min=0.5,
            electride_depth_min=0.2,
            electride_charge_min=0.3,
            electride_volume_min=10,
            electride_radius_min=0.3,
            radius_refine_method="linear",
            write_results=True,
        ),
    ):
        if partitioning_grid.structure != charge_grid.structure:
            raise ValueError("Grid structures must be the same.")
        if threads is None:
            self.threads = math.floor(psutil.Process().num_threads() * 0.9 / 2)
        else:
            self.threads = threads

        # Check if POTCAR exists in path. If not, throw warning
        if not (directory / "POTCAR").exists():
            # BUG: This will need to be changed to allow BadELF to be performed
            # on results from programs other than VASP
            raise Exception(
                """
                No POTCAR file found in the requested directory. This
                is needed to calculate oxidation states
                """
            )
        if algorithm not in ["badelf", "voronelf", "zero-flux"]:
            raise ValueError(
                """The algorithm setting you chose does not exist. Please select
                  either 'badelf', 'voronelf', or 'zero-flux'.
                  """
            )
        self.partitioning_grid = partitioning_grid
        self.separate_spin = separate_spin
        self.charge_grid = charge_grid
        self.directory = directory
        self.algorithm = algorithm
        self.find_electrides = find_electrides
        self.shared_feature_algorithm = shared_feature_algorithm
        self.ignore_low_pseudopotentials = ignore_low_pseudopotentials
        self.elf_analyzer_kwargs = elf_analyzer_kwargs

        # Create badelf class variables for each spin
        self.spin_polarized = False
        if separate_spin and partitioning_grid.is_spin_polarized:
            # BUG This assumes the partitioning grid is ELF. This should usually
            # be the case, but someone may want to use the voronoi method with
            # charge density
            partitioning_grid_up, partitioning_grid_down = (
                partitioning_grid.split_to_spin()
            )
            self.partitioning_grid_up, self.partitioning_grid_down = (
                partitioning_grid_up,
                partitioning_grid_down,
            )
            charge_grid_up, charge_grid_down = charge_grid.split_to_spin("charge")
            self.charge_grid_up, self.charge_grid_down = (
                charge_grid_up,
                charge_grid_down,
            )
            # check that our ELF isn't identical. If it is, we can perform a
            # single non-polarized calculation
            if not np.allclose(
                self.partitioning_grid_up.total,
                self.partitioning_grid_down.total,
                rtol=0,
                atol=0.001,
            ):
                self.spin_polarized = True
        # Now check if we should run a spin polarized badelf calc or not
        if self.spin_polarized:
            elf_analyzer_kwargs["plot_name"] = "bifurcation_plot_up"
            self.badelf_spin_up = BadElfToolkit(
                partitioning_grid=partitioning_grid_up,
                charge_grid=charge_grid_up,
                directory=directory,
                threads=threads,
                algorithm=algorithm,
                shared_feature_separation_method=shared_feature_separation_method,
                shared_feature_algorithm=shared_feature_algorithm,
                find_electrides=find_electrides,
                labeled_structure=labeled_structure_up,
                ignore_low_pseudopotentials=ignore_low_pseudopotentials,
                downscale_resolution=downscale_resolution,
                elf_analyzer_kwargs=elf_analyzer_kwargs,
            )
            elf_analyzer_kwargs["plot_name"] = "bifurcation_plot_down"
            self.badelf_spin_down = BadElfToolkit(
                partitioning_grid=partitioning_grid_down,
                charge_grid=charge_grid_down,
                directory=directory,
                threads=threads,
                algorithm=algorithm,
                shared_feature_separation_method=shared_feature_separation_method,
                shared_feature_algorithm=shared_feature_algorithm,
                find_electrides=find_electrides,
                labeled_structure=labeled_structure_up,
                ignore_low_pseudopotentials=ignore_low_pseudopotentials,
                downscale_resolution=downscale_resolution,
                elf_analyzer_kwargs=elf_analyzer_kwargs,
            )
        else:
            self.badelf_spin_up = BadElfToolkit(
                partitioning_grid=partitioning_grid,
                charge_grid=charge_grid,
                directory=directory,
                threads=threads,
                algorithm=algorithm,
                shared_feature_separation_method=shared_feature_separation_method,
                shared_feature_algorithm=shared_feature_algorithm,
                find_electrides=find_electrides,
                labeled_structure=labeled_structure_up,
                ignore_low_pseudopotentials=ignore_low_pseudopotentials,
                downscale_resolution=downscale_resolution,
                elf_analyzer_kwargs=elf_analyzer_kwargs,
            )
            self.badelf_spin_down = None

    @property
    def badelf_spin_up_results(self):
        return self.badelf_spin_up.results

    @property
    def badelf_spin_down_results(self):
        if self.badelf_spin_down is not None:
            return self.badelf_spin_down.results
        else:
            return None

    @cached_property
    def all_atom_elf_radii(self):
        """
        The elf radii for all atoms-neighbor pairs in the structure. Atom neighbor
        pairs are obtained using CrystalNN while the radii are obtained during
        the partitioning process.
        """
        return self._get_all_atom_elf_radii()

    def _get_all_atom_elf_radii(self):
        """
        Gets the elf radii for all atom-neighbor pairs in the structure.
        If spin is separated, takes an average for each atom.
        """
        if self.algorithm == "zero-flux":
            logging.warn(
                "Elf ionic radii are not calculated when using zero-flux partitioning."
            )
            return None
        if self.spin_polarized:
            spin_up_radii = self.badelf_spin_up.all_atom_elf_radii
            spin_down_radii = self.badelf_spin_down.all_atom_elf_radii
            radii = [
                (i + j) / 2
                for i, j in zip(spin_up_radii["radius"], spin_down_radii["radius"])
            ]
            average_radii = spin_up_radii.copy()
            average_radii["radius"] = radii
            return average_radii
        else:
            return self.badelf_spin_up.all_atom_elf_radii

    def write_atom_elf_radii(self, filename: str = "elf_radii.csv"):
        """
        Writes atomic elf radii to a csv.
        """
        if ".csv" not in filename:
            filename += ".csv"
        if self.all_atom_elf_radii is not None:
            self.all_atom_elf_radii.to_csv(self.directory / filename)
        else:
            logging.warn(
                "Elf ionic radii could not be found (likely due to zero-flux partitioning). No radii will be written."
            )

    @cached_property
    def results(self):
        return self._get_results()

    def _get_results(self):
        # If this calculation isn't spin polarized, just return the results from
        # the "spin up" badelf.
        if not self.spin_polarized:
            results = self.badelf_spin_up_results
            results["separate_spin"] = self.separate_spin
            return results
        # otherwise we want to combine our results
        logging.info("Getting results for spin-up")
        spin_up_results = self.badelf_spin_up_results
        logging.info("Getting results for spin-down")
        spin_down_results = self.badelf_spin_down_results
        # get structures for each
        structure = self.partitioning_grid.structure.copy()
        spin_up_structure = spin_up_results["labeled_structure"]
        spin_down_structure = spin_down_results["labeled_structure"]
        # Some results will be the same regardless of spin. We get these first
        nelectrons_up = spin_up_results["nelectrons"]
        nelectrons_down = spin_down_results["nelectrons"]
        results = {}
        results["algorithm"] = spin_up_results["algorithm"]
        results["nelectrons"] = nelectrons_up + nelectrons_down
        results["structure"] = structure
        results["shared_feature_algorithm"] = spin_up_results[
            "shared_feature_algorithm"
        ]
        results["shared_feature_separation_method"] = spin_up_results[
            "shared_feature_separation_method"
        ]
        results["separate_spin"] = self.separate_spin
        results["differing_spin"] = self.spin_polarized

        # Some results will be the same if we have identical structures
        nshared_features_up = spin_up_results["nshared_features"]
        nelectrides_up = spin_up_results["nelectrides"]
        nshared_features_down = spin_down_results["nshared_features"]
        nelectrides_down = spin_down_results["nelectrides"]

        if spin_up_structure == spin_down_structure:
            results["labeled_structure"] = spin_up_structure
            results["atom_coord_envs"] = spin_up_results["atom_coord_envs"]
            results["electride_coord_envs"] = spin_up_results["electride_coord_envs"]
            results["shared_feature_coord_envs"] = spin_up_results[
                "shared_feature_coord_envs"
            ]
            results["nshared_features"] = spin_up_results["nshared_features"]
            results["nelectrides"] = spin_up_results["nelectrides"]
            results["shared_feature_atoms"] = spin_up_results["shared_feature_atoms"]
            results["shared_feature_types"] = spin_up_results["shared_feature_types"]

        # Otherwise they will be different and need to be stored in separate keys
        else:
            # Spin up
            results["labeled_structure_up"] = spin_up_results["labeled_structure"]
            results["nshared_features_up"] = nshared_features_up
            results["nelectrides_up"] = nelectrides_up
            results["shared_feature_atoms_up"] = spin_up_results["shared_feature_atoms"]
            results["atom_coord_envs_up"] = spin_up_results["atom_coord_envs"]
            results["electride_coord_envs_up"] = spin_up_results["electride_coord_envs"]
            results["shared_feature_coord_envs_up"] = spin_up_results[
                "shared_feature_coord_envs"
            ]
            results["shared_feature_types_up"] = spin_up_results["shared_feature_types"]
            # Spin down
            results["labeled_structure_down"] = spin_down_results["labeled_structure"]
            results["nshared_features_down"] = nshared_features_down
            results["nelectrides_down"] = nelectrides_down
            results["shared_feature_atoms_down"] = spin_down_results[
                "shared_feature_atoms"
            ]
            results["atom_coord_envs_down"] = spin_down_results["atom_coord_envs"]
            results["electride_coord_envs_down"] = spin_down_results[
                "electride_coord_envs"
            ]
            results["shared_feature_coord_envs_down"] = spin_down_results[
                "shared_feature_coord_envs"
            ]
            results["shared_feature_types_down"] = spin_down_results[
                "shared_feature_types"
            ]

        # Other results should be stored separately regardless of if the structure
        # is the same
        atom_charges_up = spin_up_results["atom_charges"]
        electride_charges_up = spin_up_results["electride_charges"]
        shared_feature_charges_up = spin_up_results["shared_feature_charges"]
        atom_volumes_up = spin_up_results["atom_volumes"]
        electride_volumes_up = spin_up_results["electride_volumes"]
        shared_feature_volumes_up = spin_up_results["shared_feature_volumes"]
        electride_oxidation_states_up = spin_up_results["electride_oxidation_states"]

        atom_volumes_down = spin_down_results["atom_volumes"]
        electride_volumes_down = spin_down_results["electride_volumes"]
        shared_feature_volumes_down = spin_down_results["shared_feature_volumes"]
        atom_charges_down = spin_down_results["atom_charges"]
        electride_charges_down = spin_down_results["electride_charges"]
        shared_feature_charges_down = spin_down_results["shared_feature_charges"]
        electride_oxidation_states_down = spin_down_results[
            "electride_oxidation_states"
        ]
        # up
        results["electride_dim_cutoffs_up"] = spin_up_results["electride_dim_cutoffs"]
        results["electride_dim_up"] = spin_up_results["electride_dim"]
        results["atom_min_dists_up"] = spin_up_results["atom_min_dists"]
        results["electride_min_dists_up"] = spin_up_results["electride_min_dists"]
        results["shared_feature_min_dists_up"] = spin_up_results[
            "shared_feature_min_dists"
        ]
        results["atom_elf_maxima_up"] = spin_up_results["atom_elf_maxima"]
        results["electride_elf_maxima_up"] = spin_up_results["electride_elf_maxima"]
        results["shared_feature_elf_maxima_up"] = spin_up_results[
            "shared_feature_elf_maxima"
        ]
        results["atom_charges_up"] = atom_charges_up
        results["electride_charges_up"] = electride_charges_up
        results["electride_oxidation_states_up"] = electride_oxidation_states_up
        results["shared_feature_charges_up"] = shared_feature_charges_up
        results["atom_volumes_up"] = atom_volumes_up
        results["electride_volumes_up"] = electride_volumes_up
        results["shared_feature_volumes_up"] = shared_feature_volumes_up
        results["nelectrons_up"] = nelectrons_up
        results["bifurcation_graph_up"] = spin_up_results["bifurcation_graph"]

        # down
        results["electride_dim_cutoffs_down"] = spin_down_results[
            "electride_dim_cutoffs"
        ]
        results["electride_dim_down"] = spin_down_results["electride_dim"]
        results["atom_min_dists_down"] = spin_down_results["atom_min_dists"]
        results["electride_min_dists_down"] = spin_down_results["electride_min_dists"]
        results["shared_feature_min_dists_down"] = spin_down_results[
            "shared_feature_min_dists"
        ]
        results["atom_elf_maxima_down"] = spin_down_results["atom_elf_maxima"]
        results["electride_elf_maxima_down"] = spin_down_results["electride_elf_maxima"]
        results["shared_feature_elf_maxima_down"] = spin_down_results[
            "shared_feature_elf_maxima"
        ]
        results["atom_charges_down"] = atom_charges_down
        results["electride_charges_down"] = electride_charges_down
        results["electride_oxidation_states_down"] = electride_oxidation_states_down
        results["shared_feature_charges_down"] = shared_feature_charges_down
        results["atom_volumes_down"] = atom_volumes_down
        results["electride_volumes_down"] = electride_volumes_down
        results["shared_feature_volumes_down"] = shared_feature_volumes_down
        results["nelectrons_down"] = nelectrons_down
        results["bifurcation_graph_down"] = spin_down_results["bifurcation_graph"]

        # Other results require a combination of both results
        # First we calculate the total oxidation state
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            potcars = Potcar.from_file(self.directory / "POTCAR")
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data.update({potcar.element: potcar.nelectrons})
        atom_oxidation_states = []
        for atom_idx, site in enumerate(structure):
            # get element name
            element_str = site.specie.symbol
            atom_charge = (
                spin_up_results["atom_charges"][atom_idx]
                + spin_down_results["atom_charges"][atom_idx]
            )
            oxi_state = round((nelectron_data[element_str] - atom_charge), 4)
            atom_oxidation_states.append(oxi_state)
        results["atom_oxidation_states"] = atom_oxidation_states

        # get the charges on each non-atomic site. If the structures are identical
        # we return these as one. Otherwise we return the separate charges.
        if spin_up_structure == spin_down_structure:
            # get electride charges and oxidation states
            electride_charges = [
                i + j for i, j in zip(electride_charges_up, electride_charges_down)
            ]
            results["electride_charges"] = electride_charges
            electride_oxidation_states = [
                i + j
                for i, j in zip(
                    electride_oxidation_states_up, electride_oxidation_states_down
                )
            ]
            results["electride_oxidation_states"] = electride_oxidation_states
            # get other feature charges
            shared_feature_charges = [
                i + j
                for i, j in zip(shared_feature_charges_up, shared_feature_charges_down)
            ]
            results["shared_feature_charges"] = shared_feature_charges
        # Calculate the "vacuum charge" or the charge not associated with any atom.
        # Also calculate the vacuum volume for each spin.
        # Ideally these should be 0.
        total_electrons = 0
        for site in structure:
            site_valence_electrons = nelectron_data[site.specie.symbol]
            total_electrons += site_valence_electrons
        total_volume_up = 0
        total_volume_down = 0
        for volumes_up in [
            atom_volumes_up,
            electride_volumes_up,
            shared_feature_volumes_up,
        ]:
            for volume in volumes_up:
                total_volume_up += volume
        for volumes_down in [
            atom_volumes_down,
            electride_volumes_down,
            shared_feature_volumes_down,
        ]:
            for volume in volumes_down:
                total_volume_down += volume

        results["vacuum_charge"] = round(
            total_electrons - (nelectrons_up + nelectrons_down), 4
        )
        results["vacuum_volume_up"] = round(
            spin_up_structure.volume - total_volume_up, 4
        )
        results["vacuum_volume_down"] = round(
            spin_up_structure.volume - total_volume_down, 4
        )

        # Calculate electrides per formula
        electrides_per_formula_up = spin_up_results.get("electrides_per_formula", 0)
        electrides_per_formula_down = spin_down_results.get("electrides_per_formula", 0)
        electrides_per_reduced_formula_up = spin_up_results.get(
            "electrides_per_reduced_formula", 0
        )
        electrides_per_reduced_formula_down = spin_down_results.get(
            "electrides_per_reduced_formula", 0
        )
        results["electrides_per_formula"] = (
            electrides_per_formula_up + electrides_per_formula_down
        )
        results["electrides_per_reduced_formula"] = (
            electrides_per_reduced_formula_up + electrides_per_reduced_formula_down
        )

        # Finally, we convert our labeled structures to a json format so that
        # they can be easily read from the database if needed.
        for key in [
            "labeled_structure",
            "labeled_structure_up",
            "labeled_structure_down",
        ]:
            struc = results.get(key, None)
            if struc is not None:
                results[key] = struc.to_json()
        for key in [
            "bifurcation_graph",
            "bifurcation_graph_up",
            "bifurcation_graph_down",
        ]:
            graph = results.get(key, None)
            if graph is not None:
                results[key] = graph.to_json()

        return results

    @classmethod
    def from_files(
        cls,
        directory: Path = Path("."),
        partitioning_file: str = "ELFCAR",
        charge_file: str = "CHGCAR",
        separate_spin: bool = True,
        algorithm: Literal["badelf", "voronelf", "zero-flux"] = "badelf",
        find_electrides: bool = True,
        labeled_structure_up: Structure = None,
        labeled_structure_down: Structure = None,
        threads: int = None,
        shared_feature_separation_method: Literal[
            "plane", "pauling", "equal"
        ] = "pauling",
        shared_feature_algorithm: Literal["zero-flux", "voronoi"] = "zero-flux",
        ignore_low_pseudopotentials: bool = False,
        downscale_resolution: int = 1200,
        elf_analyzer_kwargs: dict = dict(
            resolution=0.01,
            include_lone_pairs=False,
            metal_depth_cutoff=0.1,
            min_covalent_angle=135,
            min_covalent_bond_ratio=0.4,
            shell_depth=0.05,
            electride_elf_min=0.5,
            electride_depth_min=0.2,
            electride_charge_min=0.3,
            electride_volume_min=10,
            electride_radius_min=0.3,
            radius_refine_method="linear",
            write_results=True,
        ),
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
            separate_spin (bool):
                Whether or not to treat spin-up and spin-down separately
            algorithm (str):
                The algorithm to use. Options are "badelf", "voronelf", or "zero-flux"
            find_electrides (bool):
                Whether or not to search for electrides in the system
            labeled_structure_up:
                A pymatgen structure object with dummy atoms representing
                electride, covalent, and metallic features for the spin-up
                system
            labeled_structure_down:
                A pymatgen structure object with dummy atoms representing
                electride, covalent, and metallic features for the spin-down
                system
            thread (int):
                The number of threads to use for analysis
            shared_feature_separation_method (str):
                The method of assigning charge from shared ELF features
                such as covalent or metallic bonds.
            shared_feature_algorithm (str):
                The algorithm to use for calculating charge on covalent
                and metallic bonds. Options are "zero-flux" or "voronoi"
            ignore_low_pseudopotentials (bool):
                Whether to ignore warnings about missing atomic basins
                due to using pseudopotentials with a small amount of
                valence electrons.
            downscale_resolution (int):
                The resolution in voxels/Angstrom^3 that the grids should be
                downscaled to in the ElfAnalysisToolkit
            elf_analyzer_kwargs (dict):
                A dictionary of keyword arguments to pass to the ElfAnalyzerToolkit
                class.


        Returns:
            A BadElfToolkit instance.
        """

        partitioning_grid = Grid.from_file(directory / partitioning_file)
        charge_grid = Grid.from_file(directory / charge_file)
        return SpinBadElfToolkit(
            partitioning_grid=partitioning_grid,
            charge_grid=charge_grid,
            directory=directory,
            separate_spin=separate_spin,
            algorithm=algorithm,
            find_electrides=find_electrides,
            threads=threads,
            shared_feature_separation_method=shared_feature_separation_method,
            shared_feature_algorithm=shared_feature_algorithm,
            ignore_low_pseudopotentials=ignore_low_pseudopotentials,
            elf_analyzer_kwargs=elf_analyzer_kwargs,
            downscale_resolution=downscale_resolution,
        )

    def write_results_csv(self):
        directory = self.directory
        results = self.results
        with open(directory / "badelf_summary.csv", "w") as csv_file:
            writer = csv.writer(csv_file)
            for key, value in results.items():
                writer.writerow([key, value])

    def write_species_file(self, file_type: str = "ELFCAR", species: str = "E"):
        """
        Writes an ELFCAR or CHGCAR for a given species. Writes to the default
        directory provided to the BadelfToolkit class.

        Args:
            file_type (str):
                The type of file that you want, either ELFCAR or CHGCAR
            species (str):
                The species to write data for.

        Returns:
            None
        """
        self.badelf_spin_up.write_species_file(file_type, species)
        if self.spin_polarized:
            # rename with "up" so we don't overwrite
            os.rename(
                self.directory / f"{file_type}_{species}",
                self.directory / f"{file_type}_{species}_up",
            )
            # Write the spin down file and change the name
            self.badelf_spin_down.write_species_file(file_type, species)
            os.rename(
                self.directory / f"{file_type}_{species}",
                self.directory / f"{file_type}_{species}_down",
            )

    def write_labeled_structures(self, file_name: str = None, file_type: str = "cif"):
        """
        Writes the structure labeled with the ELF features to file.

        Args:
            file_name (str):
                The base name to use for the file. The reduced formula
                will be used if not provided.
            file_type (str):
                The type of file that you want. Allowed types are those
                allowed by pymatgen (e.g. POSCAR, cif)

        Returns:
            None
        """
        if file_name is None:
            file_name = self.partitioning_grid.structure.composition.reduced_formula
        self.badelf_spin_up.write_labeled_structure(
            f"{file_name}_labeled_up", file_type
        )
        if self.spin_polarized:
            self.badelf_spin_down.write_labeled_structure(
                f"{file_name}_labeled_down", file_type
            )
