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

from baderkit.core import ElfLabeler, Grid, Bader
from baderkit.core.labelers.bifurcation_graph.enum_and_styling import FeatureType, FEATURE_DUMMY_ATOMS

from simmate.apps.badelf.core.partitioning import PartitioningToolkit
from simmate.apps.badelf.core.voxel_assignment import VoxelAssignmentToolkit
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
        elf_labeler_kwargs (dict):
            A dictionary of keyword arguments to pass to the ElfAnalyzerToolkit
            class.

    """

    def __init__(
        self,
        partitioning_grid: Grid,
        charge_grid: Grid,
        threads: int = None,
        algorithm: Literal["badelf", "voronelf", "zero-flux"] = "badelf",
        shared_feature_splitting_method: Literal[
            "plane", "weighted_dist", "pauling", "equal", "dist", "nearest"
        ] = "plane",
        labeled_structure: Structure = None,
        crystalnn_kwargs: dict = {
            "distance_cutoffs": None,
            "x_diff_weight": 0.0,
            "porous_adjustment": False,
            },
        elf_labeler_kwargs: dict = {
            "ignore_low_pseuodpotentials" : False,
            },
    ):
        if partitioning_grid.structure != charge_grid.structure:
            raise ValueError("Grid structures must be the same.")
        if threads is None:
            self.threads = math.floor(psutil.Process().num_threads() * 0.9 / 2)
        else:
            self.threads = threads

        # Check if POTCAR exists in path. If not, throw warning
        # if not (directory / "POTCAR").exists():
        #     raise Exception(
        #         """
        #         No POTCAR file found in the requested directory.
        #         """
        #     )
        if algorithm not in ["badelf", "voronelf", "zero-flux"]:
            raise ValueError(
                """The algorithm setting you chose does not exist. Please select
                  either 'badelf', 'voronelf', or 'zero-flux'.
                  """
            )

        self.partitioning_grid = partitioning_grid
        self.charge_grid = charge_grid
        self.algorithm = algorithm
        self.crystalnn_kwargs = crystalnn_kwargs
        self.cnn = CrystalNN(**crystalnn_kwargs)

        # make sure the user isn't trying to split features with the plane method
        # while using the zero-flux method
        if shared_feature_splitting_method == "plane" and algorithm == "zero-flux":
            logging.warning(
                "The `plane` separation method cannot be used with the zero-flux algorithm. Defaulting to pauling method."
            )
            self.shared_feature_separation_method = "pauling"

        else:
            self.shared_feature_splitting_method = shared_feature_splitting_method

        
        # if a labeled structure is provided, use that instead of the elf labeler
        if labeled_structure is not None:
            self._labeled_structure = labeled_structure
            self.elf_labeler = None
            self.elf_labeler_kwargs = None
            self.bader = Bader(**self.elf_labeler_kwargs)
        else:
            self._labeled_structure = None
            self.elf_labeler_kwargs = elf_labeler_kwargs
            self.elf_labeler = ElfLabeler(
                charge_grid=charge_grid,
                reference_grid=partitioning_grid,
                crystalnn_kwargs=crystalnn_kwargs,
                **self.elf_labeler_kwargs
                )
            self.bader = self.elf_labeler.bader
            
        # Properties that will be calculated and cached
        self._structure = None
        self._plane_partitioning_structure = None
        self._electride_structure = None

        self._partitioning = None
        self._zero_flux_feature_labels = None
        self._atom_labels = None
        self._multi_atom_mask = None
        self._multi_atom_fracs = None
        
        self._electride_dim = None
        self._all_electride_dims
        self._all_electride_dim_cutoffs = None
        
        self._nelectrons = None
        self._charges = None
        self._volumes = None

        self._electrides_per_formula = None
        self._electrides_per_reduced_formula = None
        
        self._vacuum_charge = None
        self._vacuum_volume = None
        
        self._results_summary = None

    ###########################################################################
    # Convenient Properites
    ###########################################################################

    @property
    def labeled_structure(self):
        if self._labeled_structure is None:
            self._labeled_structure = self.elf_labeler.get_feature_structure(
                included_types=FeatureType.valence_types)
        return self._labeled_structure
    
    @property
    def structure(self) -> Structure:
        if self._structure is None:
            # NOTE: We don't just use the structure from one of the grids in
            # case for some reason they differ from a provided structure from
            # the user
            structure = self.labeled_structure.copy()
            # remove all non-atomic sites
            for symbol in FEATURE_DUMMY_ATOMS.values():
                if symbol in structure.symbol_set:
                    structure.remove_species([symbol])
        return structure
    
    @property
    def electride_structure(self):
        if self._electride_structure is None:
            # create our elecride structure from our labeled structure.
            # NOTE: We don't just use the structure from the elf labeler in
            # case the user provided their own
            electride_structure = self.structure.copy()
            for site in self.labeled_structure:
                if site.specie.symbol in FeatureType.bare_types:
                    electride_structure.append(FeatureType.bare_electron.dummy_species, site.frac_coords)
            self._electride_structure = electride_structure
        return self._electride_structure
    
    @property
    def plane_partitioning_structure(self) -> Structure:
        if self._plane_partitioning_structure is None:
            # we want a structure that contains all of the atoms and features
            # we plan to separate using planes.
            if self.algorithm == "zero-flux":
                self._plane_partitioning_structure = None
            elif self.algorithm == "voronelf":
                # we always want to separate both atoms and electrides with planes
                # with this method. If the "plane" method is not selected, we
                # also want to separate shared features
                if self.shared_feature_splitting_method == "plane":
                    self._plane_partitioning_structure = self.electride_structure
                else:
                    self._plane_partitioning_structure = self.labeled_structure
            elif self.algorithm == "badelf":
                # We only want to separate the atoms with planes
                self._plane_partitioning_structure = self.structure

    @property
    def nelectrides(self):
        return len(self.electride_structure.indices_from_symbol(FeatureType.bare_electron.dummy_species))
    
    @property
    def zero_flux_feature_labels(self):
        if self._zero_flux_feature_labels is None:
            if self.elf_labeler is not None:
                self._zero_flux_feature_labels = self.elf_labeler.get_feature_labels(
                    included_features=FeatureType.valence_types,
                    return_structure=False
                    )
            else:
                _,_, self._zero_flux_feature_labels=self.bader.assign_basins_to_structure(self.labeled_structure)
        return self._zero_flux_feature_labels


    @property
    def partitioning(self):
        """
        The partitioning planes for the structure as a dictionary of dataframes.
        None if the zero-flux method is selected
        """
        if self._partitioning is None:
            self._partitioning = self._get_partitioning()
        return self.partitioning

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
                the partitioning is handled by the [BaderKit](https://github.com/SWeav02/baderkit)
                """
            )
            return None
        # Get the partitioning grid
        partitioning_grid = self.partitioning_grid.copy()
        # Now get the partitioning with the proper structure
        partitioning_grid.structure = self.plane_partitioning_structure
        labeled_grid = partitioning_grid.copy()
        labeled_grid.total = self.zero_flux_feature_labels
        partitioning = PartitioningToolkit(
            partitioning_grid, 
            labeled_grid
        ).get_partitioning()
        return partitioning

    @property
    def atom_labels(self):
        """
        A 3D array with the same shape as the charge grid indicating
        which atom/electride each grid point is assigned to
        """
        if self._atom_labels is None:
            self._get_voxel_assignments()
        return self._atom_labels

    @property
    def multi_atom_fracs(self):
        """
        An (N,M) shaped array with indices i,j where i is the voxel index
        (these are sub indices, full indices are stored in multi_site_indices)
        and j is the site. A 1 indicates that this voxel is partially shared by
        this site
        """
        if self._multi_atom_fracs is None:
            self._get_voxel_assignments()
        return self._multi_atom_fracs

    @property
    def multi_atom_mask(self):
        """
        The corresponding voxel indices for the multi_atom_fracs
        array.
        """
        if self._multi_atom_mask is None and self._multi_atom_fracs is None:
            self._get_voxel_assignments()
        return self._multi_atom_mask

    def _get_voxel_assignments(self):
        """
        Gets a dataframe of voxel assignments. The dataframe has columns
        [x, y, z, charge, sites]
        """
        logging.info("Beginning voxel assignment (this can take a while)")
        algorithm = self.algorithm
        # Get the zero-flux voxel assignments
        all_voxel_site_assignments = self.feature_labels.ravel()
        # shift voxel assignments to convention where 0 is unassigned
        all_voxel_site_assignments += 1
        if algorithm == "zero-flux":
            self._atom_labels = all_voxel_site_assignments
            self._multi_atom_fracs = np.array([])
            self._multi_atom_mask = None

        # Get the objects that we'll need to assign voxels.
        elif algorithm in ["badelf", "voronelf"]:
            charge_grid = self.charge_grid
            charge_grid.structure = self.structure
            partitioning = self.partitioning
            voxel_assignment_tools = VoxelAssignmentToolkit(
                charge_grid=charge_grid,
                electride_structure=self.labeled_structure.copy(),
                partitioning=partitioning,
                algorithm=self.algorithm,
                directory=self.directory,
                shared_feature_algorithm=self.shared_feature_algorithm,
            )
            initial_voxel_site_assignments = np.zeros(charge_grid.ngridpts)
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
            atom_labels = (
                voxel_assignment_tools.get_atom_labels(
                    initial_voxel_site_assignments
                )
            )
            
            # get assignments for voxels split by two or more sites
            multi_atom_fracs = (
                voxel_assignment_tools.get_multi_atom_fracs(
                    atom_labels.copy()
                )
            )
            self._multi_atom_fracs = multi_atom_fracs
            # reshape atom labels
            atom_labels = atom_labels.reshape(self.charge_grid.shape)
            
            # get mask at multi-atom points
            multi_atom_mask = atom_labels == 0
            self._multi_atom_mask = multi_atom_mask

            # round multi-atom fractional assignments
            multi_atom_fracs = np.round(multi_atom_fracs, 2)
            
            # get assignments from maximum fractional assignment
            multi_atom_labels = np.argmax(multi_atom_fracs, axis=1)
            
            # Shift atom labels so they start at 0
            atom_labels -= 1
            
            # assign our multi-atom points
            atom_labels[multi_atom_mask] = multi_atom_labels
            self._atom_labels = atom_labels


        logging.info("Finished voxel assignment")
        return (
            atom_labels,
            multi_atom_labels,
        )
    
    @property
    def all_electride_dims(self):
        if self._all_electride_dims is None:
            self._get_electride_dimensionality()
        return self._all_electride_dims
    
    @property
    def all_electride_dim_cutoffs(self):
        if self._all_electride_dim_cutoffs is None:
            self._get_electride_dimensionality()
        return self._all_electride_dim_cutoffs
            
    @property
    def electride_dimensionality(self):
        if self._electride_dim is None:
            self._electride_dim = self.all_electride_dims[0]

    @staticmethod
    def _get_ELF_dimensionality(grid: Grid, cutoff: float):
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

    def _get_electride_dimensionality(self):
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
        highest_dimension = self._get_ELF_dimensionality(elf_grid, 0)
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
                current_dimension = self._get_ELF_dimensionality(elf_grid, guess)
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
        self._all_electride_dims = final_dimensions
        self._all_electride_dim_cutoffs = final_connections

    @property
    def results_summary(self):
        """
        A summary of the results from a BadELF run.
        """
        if self._results_summary is None:
            results = {}
            # collect method kwargs
            method_kwargs = {
                "algorithm": self.algorithm,
                "shared_feature_separation_method": self.shared_feature_separation_method,
                "shared_feature_algorithm": self.shared_feature_algorithm,
                "crystalnn_kwargs": self.crystalnn_kwargs,
                "elf_labeler_kwargs": self.elf_labeler_kwargs,
            }
            results["method_kwargs"] = method_kwargs
            if self.bifurcation_graph is not None:
                results["bifurcation_graph"] = self.bifurcation_graph.to_json()
            else:
                results["bifurcation_graph"] = None
            
            for result in [
                "structure",
                "labeled_structure",
                "electride_structure",
                "nelectrides",
                "feature_types",
                "feature_coord_atoms",
                "feature_coord_nums",
                "feature_max_values",
                "atom_max_values",
                "all_electride_dims",
                "all_electride_dim_cutoffs",
                "electride_dimensionality",
                
                    ]:
                results[result] = getattr(self, result, None)
            self._results_summary = results
        return self._get_results()

    def _get_results(self):
        """
        Gets the results for a BadELF run and prints them to a .csv file.
        """

        #######################################################################
        # Charge and Volume Information
        #######################################################################
        # This section requires workup of the information collected through the
        # algorithm
        voxel_volume = self.charge_grid.point_volume
        charge_array = self.charge_grid.total.ravel()
        a, b, c = self.charge_grid.shape
        bader = self.bader

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
                    atom_min_dists[site] = bader.atom_min_surface_distance[site]
                else:
                    atom_min_dists[site] = get_voronoi_radius(site)
            elif site in self.electride_indices:  # site is an electride
                if self.algorithm == "voronelf":
                    electride_min_dists[site] = get_voronoi_radius(site)
                else:
                    electride_min_dists[site] = bader.atom_min_surface_distance[site]
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
                    shared_feature_min_dists[site] = bader.atom_min_surface_distance[site]
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
        if len(self.multi_atom_labels) > 0:
            split_voxel_indices = self.multi_site_indices
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
        **kwargs,
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

        Returns:
            A BadElfToolkit instance.
        """

        partitioning_grid = Grid.from_vasp(directory / partitioning_file)
        charge_grid = Grid.from_vasp(directory / charge_file)
        return BadElfToolkit(
            partitioning_grid=partitioning_grid,
            charge_grid=charge_grid,
            directory=directory,
            **kwargs
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
        separate_spin: bool = True,
        **kwargs
    ):
        if partitioning_grid.structure != charge_grid.structure:
            raise ValueError("Grid structures must be the same.")

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

        self.partitioning_grid = partitioning_grid
        self.separate_spin = separate_spin
        self.charge_grid = charge_grid
        self.directory = directory

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
            self.badelf_spin_up = BadElfToolkit(
                partitioning_grid=partitioning_grid_up,
                charge_grid=charge_grid_up,
                directory=directory,
                **kwargs
            )
            self.badelf_spin_down = BadElfToolkit(
                partitioning_grid=partitioning_grid_down,
                charge_grid=charge_grid_down,
                directory=directory,
                **kwargs
            )
        else:
            self.badelf_spin_up = BadElfToolkit(
                partitioning_grid=partitioning_grid,
                charge_grid=charge_grid,
                directory=directory,
                **kwargs
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
            results["shared_feature_coord_atoms"] = spin_up_results[
                "shared_feature_coord_atoms"
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
            results["shared_feature_coord_atoms_up"] = spin_up_results[
                "shared_feature_coord_atoms"
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
            results["shared_feature_coord_atoms_down"] = spin_down_results[
                "shared_feature_coord_atoms"
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
        results["shared_feature_max_values_up"] = spin_up_results[
            "shared_feature_max_values"
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
        results["shared_feature_max_values_down"] = spin_down_results[
            "shared_feature_max_values"
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
        **kwargs,
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


        Returns:
            A BadElfToolkit instance.
        """

        partitioning_grid = Grid.from_file(directory / partitioning_file)
        charge_grid = Grid.from_file(directory / charge_file)
        return SpinBadElfToolkit(
            partitioning_grid=partitioning_grid,
            charge_grid=charge_grid,
            directory=directory,
            **kwargs
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
