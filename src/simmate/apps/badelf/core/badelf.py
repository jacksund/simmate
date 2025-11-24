# -*- coding: utf-8 -*-

import json
import logging
import math
import os
import warnings
from pathlib import Path
from typing import Literal

import numpy as np
import psutil
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.io.vasp import Potcar
from scipy.ndimage import label
from tqdm import tqdm

from baderkit.core.utilities.file_parsers import Format
from baderkit.core import ElfLabeler, Grid, Bader, SpinElfLabeler
from baderkit.core.labelers.bifurcation_graph.enum_and_styling import FeatureType, FEATURE_DUMMY_ATOMS
from baderkit.core.bader.methods.shared_numba import get_min_avg_surface_dists, get_edges

from simmate.apps.badelf.core.partitioning import PartitioningToolkit
from simmate.apps.badelf.core.voxel_assignment import VoxelAssignmentToolkit
from simmate.toolkit import Structure


class BadElfToolkit:
    """
    A set of tools for performing BadELF, VoronELF, or Zero-Flux analysis on
    outputs from a VASP calculation. This class only performs analysis
    on one spin at a time.

    Args:
        reference_grid (Grid):
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
    _spin_system = "total"

    def __init__(
        self,
        reference_grid: Grid,
        charge_grid: Grid,
        threads: int = None,
        algorithm: Literal["badelf", "voronelf", "zero-flux"] = "badelf",
        shared_feature_splitting_method: Literal[
            "plane", "pauling", "equal", "dist", "nearest"
        ] = "plane",
        labeled_structure: Structure = None,
        crystalnn_kwargs: dict = {
            "distance_cutoffs": None,
            "x_diff_weight": 0.0,
            "porous_adjustment": False,
            },
        elf_labeler_kwargs: dict = {},
        elf_labeler: ElfLabeler = None,
    ):
        assert reference_grid.structure == charge_grid.structure, "Grid structures must be the same."
        
        if threads is None:
            self.threads = math.floor(psutil.Process().num_threads() * 0.9 / 2)
        else:
            self.threads = threads
            
        self.crystalnn_kwargs = crystalnn_kwargs
        self.cnn = CrystalNN(**crystalnn_kwargs)

        if algorithm not in ["badelf", "voronelf", "zero-flux"]:
            raise ValueError(
                """The algorithm setting you chose does not exist. Please select
                  either 'badelf', 'voronelf', or 'zero-flux'.
                  """
            )

        self.reference_grid = reference_grid
        self.charge_grid = charge_grid
        self.algorithm = algorithm

        # make sure the user isn't trying to split features with the plane method
        # while using the zero-flux method
        if shared_feature_splitting_method == "plane" and algorithm == "zero-flux":
            logging.warning(
                "The `plane` separation method cannot be used with the zero-flux algorithm. Defaulting to pauling method."
            )
            self.shared_feature_splitting_method = "pauling"

        else:
            self.shared_feature_splitting_method = shared_feature_splitting_method

        
        # if a labeled structure is provided, use that instead of the elf labeler
        if labeled_structure is not None:
            self._labeled_structure = self._get_sorted_structure(labeled_structure)
            self.elf_labeler = None
            self.elf_labeler_kwargs = None
            self.bader = Bader(**self.elf_labeler_kwargs)
        else:
            self._labeled_structure = None
            if elf_labeler is None:
                self.elf_labeler_kwargs = elf_labeler_kwargs
                self.elf_labeler = ElfLabeler(
                    charge_grid=charge_grid,
                    reference_grid=reference_grid,
                    crystalnn_kwargs=crystalnn_kwargs,
                    **self.elf_labeler_kwargs
                    )
            else:
                # use provided elf labeler
                self.elf_labeler_kwargs = None
                self.elf_labeler = elf_labeler
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
        self._all_electride_dims = None
        self._all_electride_dim_cutoffs = None
        
        self._nelectrons = None
        self._charges = None
        self._volumes = None
        
        self._min_surface_dists = None
        self._avg_surface_dists = None

        self._electrides_per_formula = None
        self._electrides_per_reduced_formula = None
        
        self._total_charge = None
        self._total_volume = None
        # TODO: Add vacuum handling to Elf Analyzer and BadELF
        # self._vacuum_charge = None
        # self._vacuum_volume = None
        
        self._results_summary = None

    ###########################################################################
    # Convenient Properites
    ###########################################################################

    @staticmethod
    def _get_sorted_structure(structure: Structure) -> Structure:
        # For our partitioning scheme, we need the structure to be ordered as
        # atoms, electrides, other. This is so that the labeled grid points map
        # to structure indices.
        bare_species = FeatureType.bare_species
        shared_species = FeatureType.shared_species
        atom_sites = []
        bare_electron_sites = []
        shared_sites = []
        for site in structure:
            symbol = site.specie.symbol
            if symbol in bare_species:
                bare_electron_sites.append(site)
            elif symbol in shared_species:
                shared_sites.append(site)
            else:
                atom_sites.append(site)
        # get empty structure
        new_structure = structure.copy()
        new_structure.remove_sites([i for i in range(len(structure))])
        # add back sites in appropriate order
        for sites_list in [atom_sites, bare_electron_sites, shared_sites]:
            for site in sites_list:
                symbol = site.specie.symbol
                coord = site.frac_coords
                new_structure.append(symbol, coord)
        return new_structure
        
    @property
    def labeled_structure(self):
        if self._labeled_structure is None:
            labeled_structure = self.elf_labeler.get_feature_structure(
                included_features=FeatureType.valence_types)
            self._labeled_structure = self._get_sorted_structure(labeled_structure)
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
        return self._plane_partitioning_structure

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
        return self._partitioning

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
                the partitioning is handled by [BaderKit](https://github.com/SWeav02/baderkit)
                """
            )
            return None
        # Get the partitioning grid
        reference_grid = self.reference_grid.copy()
        # Now get the partitioning with the proper structure
        reference_grid.structure = self.plane_partitioning_structure
        labeled_grid = reference_grid.copy()
        labeled_grid.total = self.zero_flux_feature_labels
        partitioning = PartitioningToolkit(
            reference_grid, 
            labeled_grid,
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
        algorithm = self.algorithm
        if algorithm == "zero-flux":
            self._atom_labels = self.zero_flux_feature_labels
            self._multi_atom_fracs = np.array([])
            self._multi_atom_mask = None
            # if we have an elf labeler, we can go ahead and assign charges/volumes
            # since it has an internal method
            if self.elf_labeler is not None:
                self._charges, self._volumes = self.elf_labeler.get_charges_and_volumes(
                    splitting_method=self.shared_feature_splitting_method
                    )
            return
        # make sure we've run our partitioning (for logging clarity)
        self.partitioning
        logging.info("Beginning voxel assignment")
        
        # Get the zero-flux voxel assignments
        all_voxel_site_assignments = self.zero_flux_feature_labels.ravel()
        # shift voxel assignments to convention where 0 is unassigned
        all_voxel_site_assignments += 1
        
        # Get the objects that we'll need to assign voxels.
        if algorithm in ["badelf", "voronelf"]:
            charge_grid = self.charge_grid
            charge_grid.structure = self.structure
            partitioning = self.partitioning
            voxel_assignment_tools = VoxelAssignmentToolkit(
                charge_grid=charge_grid,
                electride_structure=self.labeled_structure.copy(),
                partitioning=partitioning,
                algorithm=self.algorithm,
                shared_feature_splitting_method=self.shared_feature_splitting_method
            )
            initial_voxel_site_assignments = np.zeros(charge_grid.ngridpts, dtype=np.int64)
            if algorithm == "badelf":
                # Get the voxel assignments for each electride or covalent site
                if self.shared_feature_splitting_method == "plane":
                    # We want to separate covalent/metallic features using the
                    # partitioning planes. We only calculate distinct charge
                    # for electrides
                    feature_indices = np.array(self.labeled_structure.indices_from_symbol(FeatureType.bare_electron.dummy_species))
                else:
                    # We want to separate covalent/metallic features using some
                    # other metric, so we need to calculate distinct charge for
                    # each
                    feature_indices = np.array([i for i in range(len(self.structure), len(self.labeled_structure))])
                initial_voxel_site_assignments = np.where(
                    np.isin(
                        all_voxel_site_assignments, 
                        feature_indices + 1),
                    all_voxel_site_assignments,
                    0,
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
        elf_grid = self.reference_grid.copy()
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
    def charges(self):
        if self._charges is None:
            self._get_charges_volumes()
        return self._charges
    
    @property
    def volumes(self):
        if self._volumes is None:
            self._get_charges_volumes()
        return self._volumes
    
    def _get_site_coordination(self, site_idx):
        # for atoms/electrides we use the electride structure
        if site_idx < len(self.electride_structure):
            coordination = self.cnn.get_nn_info(
                self.electride_structure, site_idx
            )
        # for covalent/metallic features we use a dummy atom
        else:
            structure = self.structure.copy()
            structure.append("H-", self.labeled_structure.frac_coords[site_idx])
            coordination = self.cnn.get_nn_info(
                structure, -1
            )
        return [int(i["site_index"]) for i in coordination]
    
    def _get_charges_volumes(self):
        # TODO: Similar to the bader method this would be much faster if I rewrote
        # it in Numba
        all_charges = np.zeros(len(self.labeled_structure))
        all_volumes = np.zeros(len(self.labeled_structure))
        charge_array = self.charge_grid.total
        # Get charges and volumes from base assignment
        for site_idx in range(len(self.labeled_structure)):
            if self.multi_atom_mask is not None:
                voxel_mask = (self.atom_labels == site_idx) & (~self.multi_atom_mask)
            else:
                voxel_mask = self.atom_labels == site_idx
            site_charge = charge_array[voxel_mask].sum()
            site_volume = np.count_nonzero(voxel_mask) * self.charge_grid.point_volume
            all_charges[site_idx] = site_charge
            all_volumes[site_idx] = site_volume

        # Get the charge and atomic volume of each voxel with multiple site
        # assignments. These are stored as a (N,M) shaped array where N
        # is the number of split voxels and M is the number of atoms.
        if len(self.multi_atom_fracs) > 0:
            split_voxel_charge = charge_array[self.multi_atom_mask]
            # get how many sites each voxel is split by
            for site_index, assignment_array in enumerate(self.multi_atom_fracs.T):
                indices_where_assigned = np.where(assignment_array > 0)[0]
                site_charge = split_voxel_charge[indices_where_assigned]
                site_charge = site_charge * assignment_array[indices_where_assigned]
                # add charge/volume to site
                all_charges[site_index] += site_charge.sum()
                all_volumes[site_index] += np.sum(
                    assignment_array[indices_where_assigned] * self.charge_grid.point_volume
                )
        
        # convert charge to vasp standard
        all_charges /= self.charge_grid.ngridpts

        # TODO: Add weighted dist like in elf labeler method
        # assign covalent/metallic charges to atoms/electrides
        charges = all_charges[:len(self.electride_structure)]
        volumes = all_volumes[:len(self.electride_structure)]
        if self.shared_feature_splitting_method == "plane":
            # we shouldn't find any charge/volume for our shared features because
            # we assigned them based on planes. We can just return
            self._charges = charges
            self._volumes = volumes
        
        for site_idx in range(len(self.electride_structure), len(self.labeled_structure)):
            charge = all_charges[site_idx]
            volume = all_volumes[site_idx]
            coord_atoms = self._get_site_coordination(site_idx)
            
            method = self.shared_feature_splitting_method
            if method == "equal":
                # The charge should be shared equally between all atoms
                charge_section = charge / len(coord_atoms)
                volume_section = volume / len(coord_atoms)
                for neigh_idx in coord_atoms:
                    charges[neigh_idx] += charge_section
                    volumes[neigh_idx] += volume_section
            elif method == "pauling":
                # We want to separate charge based on pauling electronegativity
                # First, we get the electronegativities of each species. We note
                # that the electride electrons do not have electronegativities.
                # We have chosen to use the EN of hydrogen in these cases
                ens = []
                for neigh_idx in coord_atoms:
                    species = self.electride_structure[neigh_idx].specie
                    en = species.X
                    if math.isnan(en) or en == 0.0:
                        # we don't have an en for this species and we default to
                        # a guess (2.2)
                        ens.append(2.2)
                    else:
                        ens.append(en)

                # Now we convert the electronegativites to a fraction for each
                # atom. The larger the EN, the more charge the atom will recieve
                ens = np.array(ens)
                ens /= ens.sum()
                for neigh_idx, en_frac in zip(coord_atoms, ens):
                    charges[neigh_idx] += charge * en_frac
                    volumes[neigh_idx] += volume * en_frac
            elif method == "dist":
                # get the dist to each coordinated atom
                dist_matrix = self.labeled_structure.distance_matrix
                site_row = dist_matrix[site_idx]
                dists = site_row[coord_atoms]
                # invert and normalize
                dists = 1 / dists
                dists /= dists.sum()
                # add for each atom
                for coord_idx, atom in enumerate(coord_atoms):
                    charges[atom] += charge * dists[coord_idx]
                    volumes[atom] += volume * dists[coord_idx]
            elif method == "nearest":
                # just assign all charge to the nearest atom
                dist_matrix = self.labeled_structure.distance_matrix
                site_row = dist_matrix[site_idx]
                min_val = np.min(site_row[site_row>0])
                best_neigh = np.where(site_row==min_val)[0][0]
                charges[best_neigh] += charge
                volumes[best_neigh] += volume

        self._charges = charges
        self._volumes = volumes
        
    def get_oxidation_states(self, potcar_path: Path | str = "POTCAR"):
        # Check if POTCAR exists in path. If not, throw warning
        potcar_path = Path(potcar_path)
        if not potcar_path.exists():
            logging.warning("No POTCAR file found in the requested directory. Oxidation states cannot be calculated")
            return
        # get POTCAR info
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            potcars = Potcar.from_file(self.directory / "POTCAR")
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data[potcar.element] = potcar.nelectrons
        # get valence electrons for each site in the structure
        valence = np.zeros(len(self.electride_structure), dtype=np.float64)
        for i, site in enumerate(self.structure):
            valence[i] = potcar[site.specie.symbol]
        # subtract charges from valence to get oxidation
        oxidation = valence - self.charges
        return oxidation
        
    def _get_min_avg_surface_dists(self):
        if self.shared_feature_splitting_method != "plane":
            logging.warning("""
Shared feature splitting methods other than 'plane' result in surfaces surrounding
the shared features. Atom/electride surface distances may be smaller than expected.
            """)
        neigh_transforms, _ = self.charge_grid.point_neighbor_transforms
        edges = get_edges(
            labeled_array=self.atom_labels,
            neighbor_transforms=neigh_transforms,
            vacuum_mask=self.bader.vacuum_mask
            )
        self._min_surface_dists, self._avg_surface_dists = get_min_avg_surface_dists(
            labels=self.atom_labels,
            frac_coords=self.electride_structure.frac_coords,
            edge_mask=edges,
            matrix=self.charge_grid.matrix,
            max_value=np.max(self.structure.lattice.abc) * 2,
        )

    @property
    def min_surface_dists(self):
        if self._min_surface_dists is None:
            self._get_min_avg_surface_dists()
        return self._min_surface_dists
    
    @property
    def avg_surface_dists(self):
        if self._avg_surface_dists is None:
            self._get_min_avg_surface_dists()
        return self._avg_surface_dists
        
    @property
    def electrides_per_formula(self):
        if self._electrides_per_formula is None:
            electrides_per_unit = 0
            for i in range(len(self.structure),len(self.electride_structure)):
                electrides_per_unit += self.charges[i]
            self._electrides_per_formula = electrides_per_unit
        return self._electrides_per_formula
    
    @property
    def electrides_per_reduced_formula(self):
        if self._electrides_per_reduced_formula is None:
            (
                _,
                formula_reduction_factor,
            ) = self.structure.composition.get_reduced_composition_and_factor()
            self._electrides_per_reduced_formula = self.electrides_per_formula / formula_reduction_factor
        return self._electrides_per_reduced_formula
    
    @property
    def total_charge(self):
        if self._total_charge is None:
            self._total_charge = self.charges.sum()
        return self._total_charge
    
    @property
    def total_volume(self):
        if self._total_volume is None:
            self._total_volume = self.volumes.sum()
        return self._total_volume
                
    def to_dict(self, potcar_path: Path | str = "POTCAR", use_json: bool = True):
        """
        Returns a summary of results in dictionary form
        """
        results = {}
        # collect method kwargs
        method_kwargs = {
            "algorithm": self.algorithm,
            "shared_feature_splitting_method": self.shared_feature_splitting_method,
            "crystalnn_kwargs": self.crystalnn_kwargs,
            "elf_labeler_kwargs": self.elf_labeler_kwargs,
        }
        results["method_kwargs"] = method_kwargs
        
        results["oxidation_states"] = self.get_oxidation_states(potcar_path)
        
        for result in [
            "structure",
            "labeled_structure",
            "electride_structure",
            "nelectrides",
            "all_electride_dims",
            "all_electride_dim_cutoffs",
            "electride_dimensionality",
            "charges",
            "volumes",
            "min_surface_dists",
            "avg_surface_dists",
            "electrides_per_formula",
            "electrides_per_reduced_formula",
            "total_charge",
            "total_volume",
                ]:
            results[result] = getattr(self, result, None)
        if use_json:
            # get serializable versions of each attribute
            for key in ["structure", "labeled_structure", "electride_structure"]:
                results[key] = results[key].to_json()
            for key in ["charges", "volumes", "oxidation_states", "min_surface_dists", "avg_surface_dists"]:
                if results[key] is None:
                    continue # skip oxidation states if they fail
                results[key] = results[key].tolist()        
        return results
                
    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(use_json=True, **kwargs))
    
    def write_results_summary(self, filepath: Path | str = "badelf_results_summary.json", **kwargs):
        filepath = Path(filepath)
        with open(filepath, "w") as json_file:
            json.dump(self.to_dict(use_json=True, **kwargs), json_file, indent=4)

    @classmethod
    def from_vasp(
        cls,
        reference_file: str | Path = "ELFCAR",
        charge_file: str | Path = "CHGCAR",
        **kwargs,
    ):
        """
        Creates a BadElfToolkit instance from the requested partitioning file
        and charge file.

        Parameters
        ----------
        reference_file : str | Path, optional
            The path to the file to use for partitioning. Must be a VASP
            CHGCAR or ELFCAR type file. The default is "ELFCAR".
        charge_file : str | Path, optional
            The path to the file containing the charge density. Must be a VASP
            CHGCAR or ELFCAR type file. The default is "CHGCAR".
        **kwargs : any
            Additional keyword arguments for the BadElfToolkit class.

        Returns
        -------
        BadElfToolkit
            A BadElfToolkit instance.
        """

        reference_grid = Grid.from_vasp(reference_file)
        charge_grid = Grid.from_vasp(charge_file)
        return cls(
            reference_grid=reference_grid,
            charge_grid=charge_grid,
            **kwargs
        )

    def write_species_file(
            self, 
            directory: str | Path = None,
            write_reference: bool = True,
            species: str = FeatureType.bare_electron.dummy_species,
            include_dummy_atoms: bool = True,
            output_format: str | Format = None,
            prefix_override: str = None,
            ):
        """
        Writes an ELFCAR or CHGCAR for a given species. Writes to the default
        directory provided to the BadelfToolkit class.

        Args:
            directory : str | Path
                The directory to write the files in. If None, the active directory
                is used.
            write_reference : bool, optional
                Whether or not to write the reference data rather than the charge data.
                Default is True.
            species (str):
                The species to write data for.
            include_dummy_atoms : bool, optional
                Whether or not to add dummy files to the structure. The default is False.
            output_format : str | Format, optional
                The format to write with. If None, writes to source format stored in
                the Grid objects metadata.
                Defaults to None.
            prefix_override : str, optional
                The string to add at the front of the output path. If None, defaults
                to the VASP file name equivalent to the data type stored in the
                grid.
                
        Returns:
            None
        """
        if directory is None:
            directory = Path(".")
        
        # Get voxel assignments and data
        voxel_assignment_array = self.atom_labels
        if write_reference:
            grid = self.reference_grid.copy()
        else:
            grid = self.charge_grid.copy()
        
        # add dummy atoms if desired
        indices = self.electride_structure.indices_from_symbol(species)
        if include_dummy_atoms:
            grid.structure = self.electride_structure
        # Get mask where the grid belongs to requested species
        mask = np.isin(voxel_assignment_array, indices,invert=True)
        grid.total[mask] = 0
        if grid.diff is not None:
            grid.diff[mask] = 0

        # get prefix
        if prefix_override is None:
            prefix_override = grid.data_type.prefix
        
        file_path = directory / f"{prefix_override}_{species}"
        # write file
        grid.write(filename=file_path, output_format=output_format)

    def write_atom_file(
        self, 
        atom_index: int,
        directory: str | Path = None,
        write_reference: bool = True,
        include_dummy_atoms: bool = True,
        output_format: str | Format = None,
        prefix_override: str = None,
    ):
        """
        Writes an ELFCAR or CHGCAR for a given atom/electride. Writes to the default
        directory provided to the BadelfToolkit class.

        Args:
            atom_index (int):
                The index of the atom/electride to write for.
            directory : str | Path
                The directory to write the files in. If None, the active directory
                is used.
            write_reference : bool, optional
                Whether or not to write the reference data rather than the charge data.
                Default is True.
            include_dummy_atoms : bool, optional
                Whether or not to add dummy files to the structure. The default is False.
            output_format : str | Format, optional
                The format to write with. If None, writes to source format stored in
                the Grid objects metadata.
                Defaults to None.
            prefix_override : str, optional
                The string to add at the front of the output path. If None, defaults
                to the VASP file name equivalent to the data type stored in the
                grid.
                
        Returns:
            None
        """
        if directory is None:
            directory = Path(".")
            
        # Get voxel assignments and data
        voxel_assignment_array = self.atom_labels
        if write_reference:
            grid = self.reference_grid.copy()
        else:
            grid = self.charge_grid.copy()
        
        # add dummy atoms if desired
        if include_dummy_atoms:
            grid.structure = self.electride_structure
        
        # Get mask where the grid belongs to requested species
        mask = voxel_assignment_array == atom_index
        grid.total[mask] = 0
        if grid.diff is not None:
            grid.diff[mask] = 0

        # get prefix
        if prefix_override is None:
            prefix_override = grid.data_type.prefix
        
        file_path = directory / f"{prefix_override}_{atom_index}"
        # write file
        grid.write(filename=file_path, output_format=output_format)
        

class SpinBadElfToolkit:
    """
    This class is a wrapper for the BadElfToolkit adding the capability
    to individually handle spin-up and spin-down components of the
    ELF and charge density.
    """
    _spin_system = "combined"

    def __init__(
        self,
        reference_grid: Grid,
        charge_grid: Grid,
        labeled_structure_up: Structure = None,
        labeled_structure_down: Structure = None,
        crystalnn_kwargs: dict = {
            "distance_cutoffs": None,
            "x_diff_weight": 0.0,
            "porous_adjustment": False,
            },
        spin_elf_labeler_kwargs: dict = {},
        spin_elf_labeler: ElfLabeler = None,
        **kwargs
    ):
        # make sure our grids are spin polarized
        assert reference_grid.is_spin_polarized, "Provided grid is not spin polarized. Use the standard BadElfToolkit."

        self.reference_grid = reference_grid
        self.charge_grid = charge_grid
        
        # if a labeled structure is provided, use that instead of the elf labeler
        if labeled_structure_up is not None or labeled_structure_down is not None:
            assert labeled_structure_up is not None and labeled_structure_down is not None, "If providing a labeled structure, both up and down systems must be provided."
        # If no labeled structures are provided, we want to use the spin elf
        # labeler and link it to our badelf objects
        if labeled_structure_up is None:
            # we want to attach a SpinElfLabeler to our badelf objects
            if spin_elf_labeler is None:
                spin_elf_labeler = SpinElfLabeler(
                    charge_grid=charge_grid,
                    reference_grid=reference_grid,
                    crystalnn_kwargs=crystalnn_kwargs,
                    **spin_elf_labeler_kwargs
                    )
            self.elf_labeler = spin_elf_labeler
            # link charge grids
            self.reference_grid_up = spin_elf_labeler.reference_grid_up
            self.reference_grid_down = spin_elf_labeler.reference_grid_down
            self.charge_grid_up = spin_elf_labeler.charge_grid_up
            self.charge_grid_down = spin_elf_labeler.charge_grid_down
            self.equal_spin = spin_elf_labeler._equal_spin
            # link labelers
            self._elf_labeler_up = spin_elf_labeler.elf_labeler_up
            self._elf_labeler_down = spin_elf_labeler.elf_labeler_down
        else:
            # We won't be using a labeler so we need to split the grids
            self._elf_labeler_up = None
            self._elf_labeler_down = None
            self.equal_spin = False
            if reference_grid.is_spin_polarized:
                self.reference_grid_up, self.reference_grid_down = (
                    reference_grid.split_to_spin()
                )

                self.charge_grid_up, self.charge_grid_down = charge_grid.split_to_spin("charge")

                # check that our ELF isn't identical. If it is, we can perform a
                # single non-polarized calculation
                if not np.allclose(
                    self.reference_grid_up.total,
                    self.reference_grid_down.total,
                    rtol=0,
                    atol=0.001,
                ):
                    self.equal_spin = True
                
        # Now check if we should run a spin polarized badelf calc or not
        if self.equal_spin:
            self.badelf_up = BadElfToolkit(
                reference_grid=self.reference_grid_up,
                charge_grid=self.charge_grid_up,
                labeled_structure=labeled_structure_up,
                elf_labeler=self._elf_labeler_up
                **kwargs
            )
            self.badelf_down = BadElfToolkit(
                reference_grid=self.reference_grid_down,
                charge_grid=self.charge_grid_down,
                labeled_structure=labeled_structure_down,
                elf_labeler=self._elf_labeler_down,
                **kwargs
            )
            self.badelf_up._spin_system = "up"
            self.badelf_down._spin_system = "down"
        else:
            self.badelf_up = BadElfToolkit(
                reference_grid=reference_grid,
                charge_grid=charge_grid,
                labeled_structure=labeled_structure_up,
                elf_labeler=self._elf_labeler_up
                **kwargs
            )
            self.badelf_up._spin_system = "half"
            self.badelf_down = self.badelf_up
            
        # Properties that will be calculated and cached
        self._electride_structure = None
        self._labeled_structure = None
        
        self._electride_dim = None
        
        self._nelectrons = None
        self._charges = None
        self._volumes = None
        
        self._min_surface_dists = None
        self._avg_surface_dists = None

        self._electrides_per_formula = None
        self._electrides_per_reduced_formula = None
        
        self._total_charge = None
        self._total_volume = None
        # TODO: Add vacuum handling to Elf Analyzer and BadELF
        # self._vacuum_charge = None
        # self._vacuum_volume = None
        
        self._results_summary = None
        
    @property
    def structure(self):
        return self.badelf_up.structure
    
    @property
    def labeled_structure(self):
        if self._labeled_structure is None:
            # start with only atoms
            labeled_structure = self.structure.copy()
            # get up and downs structures
            structure_up = self.badelf_up.labeled_structure
            structure_down = self.badelf_down.labeled_structure
            # get species from the spin up system
            new_species = []
            new_coords = []
            for site in structure_up[len(self.structure) :]:
                species = site.specie.symbol
                # add frac coords no matter what
                new_coords.append(site.frac_coords)
                # if this site is in the spin-down structure, it exists in both and
                # we add the site with the original species name
                if site in structure_down:
                    new_species.append(species)
                else:
                    # otherwise, we rename the species
                    new_species.append(species + "xu")
            # do the same for the spin down system
            for site in structure_down[len(self.structure) :]:
                # only add the structure if it didn't exist in the spin up system
                if site not in structure_up:
                    species = site.specie.symbol
                    new_species.append(species + "xd")
                    new_coords.append(site.frac_coords)
            # add our sites
            for species, coords in zip(new_species, new_coords):
                labeled_structure.append(species, coords)
            self._labeled_structure = labeled_structure
        return self._labeled_structure
    
    @property
    def electride_structure(self) -> Structure:
        """
        The combined quasi atom structure from both the spin-up and spin-down system. Features
        found at the same fractional coordinates are combined, while those at
        different coordinates are labeled separately
        """
        if self._electride_structure is None:
            # start with only atoms
            labeled_structure = self.structure.copy()
            # get up and downs structures
            structure_up = self.badelf_up.electride_structure
            structure_down = self.badelf_down.electride_structure
            # get species from the spin up system
            new_species = []
            new_coords = []
            for site in structure_up[len(self.structure) :]:
                species = site.specie.symbol
                # add frac coords no matter what
                new_coords.append(site.frac_coords)
                # if this site is in the spin-down structure, it exists in both and
                # we add the site with the original species name
                if site in structure_down:
                    new_species.append(species)
                else:
                    # otherwise, we rename the species
                    new_species.append(species + "xu")
            # do the same for the spin down system
            for site in structure_down[len(self.structure) :]:
                # only add the structure if it didn't exist in the spin up system
                if site not in structure_up:
                    species = site.specie.symbol
                    new_species.append(species + "xd")
                    new_coords.append(site.frac_coords)
            # add our sites
            for species, coords in zip(new_species, new_coords):
                labeled_structure.append(species, coords)
            self._electride_structure = labeled_structure

        return self._electride_structure
    
    @property
    def electride_dimensionality(self):
        return max(self.badelf_up.electride_dimensionality, self.badelf_down.electride_dimensionality)

    def _get_charges_and_volumes(self):
        """
        NOTE: Volumes may not have a physical meaning when differences are found
        between spin up/down systems. They are calculated as the average between
        the systems.
        """
        # get the initial charges/volumes from the spin up system
        charges = self.badelf_up.charges.tolist()
        volumes = self.badelf_up.volumes.tolist()

        # get the charges from the spin down system
        charges_down = self.badelf_down.charges.tolist()
        volumes_down = self.badelf_down.volumes.tolist()

        # get structures from each system
        structure_up = self.badelf_up.electride_structure
        structure_down = self.badelf_down.electride_structure
        
        # add charge from spin down structure
        for site, charge, volume in zip(structure_down, charges_down, volumes_down):
            if site in structure_up:
                index = structure_up.index(site)
                charges[index] += charge
                volumes[index] += volume
            else:
                charges.append(charge)
                volumes.append(volume)
        self._charges = np.array(charges)
        self._volumes = np.array(volumes) / 2
    
    @property
    def charges(self):
        if self._charges is None:
            self._get_charges_and_volumes()
        return self._charges
    
    @property
    def volumes(self):
        if self._volumes is None:
            self._get_charges_and_volumes()
        return self._volumes
    
    def get_oxidation_states(self, potcar_path: Path | str = "POTCAR"):
        # Check if POTCAR exists in path. If not, throw warning
        potcar_path = Path(potcar_path)
        if not potcar_path.exists():
            logging.warning("No POTCAR file found in the requested directory. Oxidation states cannot be calculated")
            return
        # get POTCAR info
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            potcars = Potcar.from_file(self.directory / "POTCAR")
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data[potcar.element] = potcar.nelectrons
        # get valence electrons for each site in the structure
        valence = np.zeros(len(self.electride_structure), dtype=np.float64)
        for i, site in enumerate(self.structure):
            valence[i] = potcar[site.specie.symbol]
        # subtract charges from valence to get oxidation
        oxidation = valence - self.charges
        return oxidation

    @property
    def electrides_per_formula(self):
        if self._electrides_per_formula is None:
            electrides_per_unit = 0
            for i in range(len(self.structure),len(self.electride_structure)):
                electrides_per_unit += self.charges[i]
            self._electrides_per_formula = electrides_per_unit
        return self._electrides_per_formula
    
    @property
    def electrides_per_reduced_formula(self):
        if self._electrides_per_reduced_formula is None:
            (
                _,
                formula_reduction_factor,
            ) = self.structure.composition.get_reduced_composition_and_factor()
            self._electrides_per_reduced_formula = self.electrides_per_formula / formula_reduction_factor
        return self._electrides_per_reduced_formula
    
    @property
    def total_charge(self):
        if self._total_charge is None:
            self._total_charge = self.charges.sum()
        return self._total_charge
    
    @property
    def total_volume(self):
        if self._total_volume is None:
            self._total_volume = self.volumes.sum()
        return self._total_volume

    def to_dict(
            self, 
            potcar_path: Path | str = "POTCAR", 
            use_json: bool = True):
        """
        Returns a summary of results in dictionary form
        """
        results = {}

        results["method_kwargs"] = self.badelf_up.to_dict()["method_kwargs"]
        
        results["oxidation_states"] = self.get_oxidation_states(potcar_path)
        
        for result in [
            "structure",
            "labeled_structure",
            "electride_structure",
            "nelectrides",
            "electride_dimensionality",
            "charges",
            "volumes",
            "electrides_per_formula",
            "electrides_per_reduced_formula",
            "total_charge",
            "total_volume",
                ]:
            results[result] = getattr(self, result, None)
        if use_json:
            # get serializable versions of each attribute
            for key in ["structure", "labeled_structure", "electride_structure"]:
                results[key] = results[key].to_json()
            for key in ["charges", "volumes", "oxidation_states"]:
                results[key] = results[key].tolist()        
        return results
                
    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(use_json=True, **kwargs))
    
    def write_results_summary(self, filepath: Path | str = "badelf_results_summary.json", **kwargs):
        filepath = Path(filepath)
        with open(filepath, "w") as json_file:
            json.dump(self.to_dict(use_json=True, **kwargs), json_file, indent=4)


    @classmethod
    def from_vasp(
        cls,
        reference_file: str | Path = "ELFCAR",
        charge_file: str | Path = "CHGCAR",
        **kwargs,
    ):
        """
        Creates a SpinBadElfToolkit instance from the requested partitioning file
        and charge file.

        Parameters
        ----------
        reference_file : str | Path, optional
            The path to the file to use for partitioning. Must be a VASP
            CHGCAR or ELFCAR type file. The default is "ELFCAR".
        charge_file : str | Path, optional
            The path to the file containing the charge density. Must be a VASP
            CHGCAR or ELFCAR type file. The default is "CHGCAR".
        **kwargs : any
            Additional keyword arguments for the SpinBadElfToolkit class.

        Returns
        -------
        SpinBadElfToolkit
            A SpinBadElfToolkit instance.
        """

        reference_grid = Grid.from_vasp(reference_file)
        charge_grid = Grid.from_vasp(charge_file)
        return cls(
            reference_grid=reference_grid,
            charge_grid=charge_grid,
            **kwargs
        )

    def write_species_file(
            self, 
            directory: str | Path = None,
            species: str = FeatureType.bare_electron.dummy_species,
            prefix_override: str = None,
            write_reference: bool = True,
            **kwargs,
            ):
        """
        Writes an ELFCAR or CHGCAR for a given species. Writes to the default
        directory provided to the BadelfToolkit class.

        Args:
            directory : str | Path
                The directory to write the files in. If None, the active directory
                is used.
            species (str):
                The species to write data for.
            prefix_override : str, optional
                The string to add at the front of the output path. If None, defaults
                to the VASP file name equivalent to the data type stored in the
                grid.
            write_reference : bool, optional
                Whether or not to write the reference data rather than the charge data.
                Default is True.
                
        Returns:
            None
        """
        
        if directory is None:
            directory = Path(".")
            
        # get prefix
        if prefix_override is None:
            if write_reference:
                prefix_override = self.reference_grid.data_type.prefix
            else:
                prefix_override = self.charge_grid.data_type.prefix
        
        self.badelf_up.write_species_file(
            species=species,
            directory=directory,
            prefix_override=prefix_override,
            **kwargs
            )
        if self.spin_polarized:
            # rename with "up" so we don't overwrite
            os.rename(
                directory / f"{prefix_override}_{species}",
                directory / f"{prefix_override}_{species}_up",
            )
            # Write the spin down file and change the name
            self.badelf_down.write_species_file(
                species=species,
                directory=directory,
                prefix_override=prefix_override,
                **kwargs
                )
            os.rename(
                directory / f"{prefix_override}_{species}",
                directory / f"{prefix_override}_{species}_down",
            )

