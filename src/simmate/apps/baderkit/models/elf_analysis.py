# -*- coding: utf-8 -*-
"""
This file contains tables related to results from the ElfLabeler class.
Since this class is often used during other workfows (e.g. BadELF) there
is some model gymnastics going on. The ElfAnalysis and SpinElfAnalysis
classes do not inherit the Calculation database intentionally to avoid
many empty entries. The ElfAnalysisCalculation and SpinElfAnalysisCalculation
models are essentially wrappers that add in the Calculation mixin and
use ForeignKeys to point to the corresponding ElfAnalysis table.

"""

from pathlib import Path

from baderkit.core import ElfLabeler, SpinElfLabeler
from baderkit.core.labelers.bifurcation_graph.enum_and_styling import FeatureType
import numpy as np

from simmate.database.base_data_types import (
    Calculation,
    Structure,
    table_column,
)

class ElfAnalysis(Structure):
    """
    This table contains data from an ELF topology analysis. It intentionally
    does not inherit from the Calculation table as the results may not
    be generated from a dedicated workflow.
    """
    
    class Meta:
        app_label = "baderkit"
    
    method_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used when labeling features in the structure
    """
    
    bifurcation_graph = table_column.JSONField(blank=True, null=True)
    """
    The bifurcation graph representing where features appear and connect
    in the ELF
    """
    
    labeled_structure = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure with dummy atoms representing the location of chemical
    features in the system.
    """

    quasi_atom_structure = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure with dummy atoms representing the location of quasi
    atoms (e.g. electrides, bare electrons, etc.)
    """
    
    atom_elf_radii = table_column.JSONField(blank=True, null=True)
    """
    The radii of each atom in the structure calculated from the ELF
    """
    
    atom_elf_radii_types = table_column.CharField(
        blank=True,
        null=True,
        max_length=25,
    )
    """
    The type of bond with the nearest neighbor, covalent or ionic
    """
    
    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states for each quasi atom.
    
    WARNING: For calculations on spin up/down systems, this will not be accurate.
    The oxidation states calculated in the SpinElfAnalysis table should be used
    instead
    """

    charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each atom and quasi
    atom.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """
    
    volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of volumes from the oxidation analysis (i.e. the bader volume)
    """
    
    spin_system = table_column.CharField(
        blank=True,
        null=True,
        max_length=25,
    )
    """
    Which type of spin this calculation was performed on i.e. up, down, total, separate
    """

    def update_from_directory(self, directory):
        """
        The base database workflow will try and register data from the local
        directory. As part of this it checks for a vasprun.xml file and
        attempts to run a from_vasp_run method. Since this is not defined for
        this model, an error is thrown. To account for this, I just create an empty
        update_from_directory method here.
        """
        pass
    
    @classmethod
    def from_labeler(
            cls, 
            labeler: ElfLabeler,
            directory: Path,
            **kwargs
            ):
        """
        Creates a new row from an ElfLabeler object
        """
        # get structure dict info
        structure_dict = cls._from_toolkit(
            structure=labeler.structure,
            as_dict=True
            )
        
        results = {}
        graph = getattr(labeler, "bifurcation_graph", None)
        if graph is not None:
            graph = graph.to_json()
        results["bifurcation_graph"] = graph
        results["labeled_structure"] = labeler.labeled_structure.to_json()
        results["quasi_atom_structure"] = labeler.quasi_atom_structure.to_json()
        results["atom_elf_radii"] = [float(i) for i in labeler.atom_elf_radii]
        results["atom_elf_radii_types"] = [str(i) for i in labeler.atom_elf_radii_types]
        results["spin_system"] = labeler._spin_system
            
        oxidation_states, charges, volumes = labeler.get_oxidation_and_volumes_from_potcar(
            potcar_path = directory / "POTCAR",
            **kwargs
            )
        results["oxidation_states"] = oxidation_states.tolist()
        results["charges"] = charges.tolist()
        results["volumes"] = volumes.tolist()
        
        # add setting kwargs
        method_kwargs = {}
        for attr in [
            "ignore_low_pseudopotentials",
            "shared_shell_ratio",
            "combine_shells",
            "min_covalent_charge",
            "min_covalent_angle",
            "min_electride_charge",
            "min_electride_depth",
            "min_electride_dist_beyond_atom",
            "min_electride_volume",
            "min_electride_elf_value",
            "crystalnn_kwargs"
                ]:
            method_kwargs[attr] = getattr(labeler, attr, None)
        results["method_kwargs"] = method_kwargs
        # create a new entry
        new_row = cls(
            **structure_dict,
            **results
            )
        new_row.save()

        # update elf features
        new_row.update_elf_features(labeler)
        
        # update radii
        new_row.update_elf_radii(labeler)
        
        return new_row

    def update_elf_features(self, labeler: ElfLabeler | SpinElfLabeler):
        # first, check if this is a spin-separated calculation. If so, we do
        # not store elf features
        if isinstance(labeler, SpinElfLabeler):
            return
        # pull all the data together and save it to the database. We
        # are saving this to an ElfIonicRadii datatable. To access this
        # model, we need to use "elf_features.model".
        feature_model = self.elf_features.model
        # Let's iterate through the ELF features and save these to the database.
        struc_len = len(labeler.structure)
        quasi_atom_count = 0
        for node_idx, node in enumerate(labeler.bifurcation_graph.irreducible_nodes):
            # get dict of all info for this feature
            new_row_dict = {}
            for entry in feature_model.get_column_names():
                test_attr = getattr(node, entry, None)
                if test_attr is None:
                    continue
                # convert numpy arrays
                if isinstance(test_attr, np.ndarray):
                    test_attr = test_attr.tolist()
                new_row_dict[entry] = test_attr
            # update values not stored directly in dict
            new_row_dict["analysis"] = self
            if node.feature_type in FeatureType.bare_types:
                new_row_dict["quasi_atom_structure_index"] = struc_len + quasi_atom_count
                quasi_atom_count += 1
            new_row_dict["labeled_structure_index"] = struc_len + node_idx
            new_row = feature_model(**new_row_dict)
            new_row.save()
            
    def update_elf_radii(self, labeler: ElfLabeler | SpinElfLabeler):
        # get radii model
        radii_model = self.atom_nn_elf_radii.model
        # get radii info
        site_indices, neigh_indices, neigh_frac_coords, neigh_dists = labeler.nearest_neighbor_data
        site_frac_coords = labeler.structure.frac_coords[site_indices]
        radii = labeler.atom_nn_elf_radii
        bond_types = labeler.atom_nn_elf_radii_types
        # create radii entries
        for idx in range(len(site_indices)):
            radii_dict = dict(
                site_index = site_indices[idx],
                neigh_index = neigh_indices[idx],
                radius = radii[idx],
                site_frac_coords = site_frac_coords[idx].tolist(),
                neigh_frac_coords = neigh_frac_coords[idx].tolist(),
                radius_type = str(bond_types[idx]),
                spin_system = labeler._spin_system,
                analysis = self,
                )
            new_radii = radii_model(**radii_dict)
            new_radii.save()        
            
class ElfAnalysisCalculation(Calculation):
    """
    This table contains results from an ELF topology analysis calculation.
    The results should be from a dedicated workflow. 
    """
    class Meta:
        app_label = "baderkit"
    
    analysis = table_column.ForeignKey(
        "baderkit.ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="calculation",
        blank=True,
        null=True,
    )
    
    def update_from_labeler(self, labeler: ElfLabeler, directory: Path, **kwargs):
        # create an entry in the ElfAnalysis table
        labeler = ElfAnalysis.from_labeler(labeler, directory)
        # link to table
        self.analysis = labeler
        self.save()



