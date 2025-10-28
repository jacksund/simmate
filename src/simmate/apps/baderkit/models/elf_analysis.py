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
    DatabaseTable,
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
    
    cutoff_kwargs = table_column.JSONField(blank=True, null=True)
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
    
    quasi_atom_elf_radii = table_column.JSONField(blank=True, null=True)
    """
    The radii of each atom and quasi atom in the structure calculated from the ELF
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
        results["bifurcation_graph"] = labeler.bifurcation_graph.to_json()
        results["labeled_structure"] = labeler.labeled_structure.to_json()
        results["quasi_atom_structure"] = labeler.quasi_atom_structure.to_json()
        results["atom_elf_radii"] = [float(i) for i in labeler.atom_elf_radii]
        results["quasi_atom_elf_radii"] = [float(i) for i in labeler.quasi_atom_elf_radii]
        results["spin_system"] = labeler._spin_system
            
        oxidation_states, charges, volumes = labeler.get_oxidation_and_volumes_from_potcar(
            potcar_path = directory / "POTCAR",
            **kwargs
            )
        results["oxidation_states"] = oxidation_states.tolist()
        results["charges"] = charges.tolist()
        results["volumes"] = volumes.tolist()
        
        # add setting kwargs
        cutoff_kwargs = {}
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
            cutoff_kwargs[attr] = getattr(labeler, attr, None)
        results["cutoff_kwargs"] = cutoff_kwargs
        # create a new entry
        new_row = cls(
            **structure_dict,
            **results
            )
        new_row.save()

        # update elf features
        new_row.update_elf_features(labeler)
        return new_row

    def update_elf_features(self, labeler: ElfLabeler):
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
            
class SpinElfAnalysis(Structure):
    """
    This table contains results from a spin-dependant ELF topology analysis
    calculation. It intentionally does not inherit from the Calculation
    table as the results may not be calculated from a dedicated workflow.
    """
    class Meta:
        app_label = "baderkit"
    
    cutoff_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used when labeling features in the structure
    """
    
    analysis_up = table_column.ForeignKey(
        "baderkit.ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="spin_analysis",
        blank=True,
        null=True,
    )
    
    analysis_down = table_column.ForeignKey(
        "baderkit.ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="spin_analysis",
        blank=True,
        null=True,
    )
    
    total_labeled_structure = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure with dummy atoms representing the location of chemical
    features in the system. This is a combination of the dummy atoms found in
    both the spin up and spin down systems.
    """

    total_quasi_atom_structure = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure with dummy atoms representing the location of quasi
    atoms (e.g. electrides, bare electrons, etc.) This is a combination of the 
    dummy atoms found in both the spin up and spin down systems.
    """
    
    average_atom_elf_radii = table_column.JSONField(blank=True, null=True)
    """
    The average of the spin up/down radii of each atom in the structure 
    calculated from the ELF
    """
    
    total_oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states for each atom and quasi atom.
    """

    total_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each quasi atom.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """
    
    average_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of quasi atom volumes from the oxidation analysis (i.e. the bader volume)
    
    WARNING: for systems with major differences between the spin up/down
    systems (e.g. magnetic systems like Y2C), the volumes may not have
    a physical meaning. The average must be taken to retain the correct
    total volume, but this reduces the size of features appearing only
    in one spin system.
    """
    
    differing_spin = table_column.BooleanField(blank=True, null=True)
    """
    Whether the spin up and spin down differ in the ELF and charge density
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
    def from_spin_labeler(
            cls, 
            labeler: SpinElfLabeler,
            directory: Path,
            **kwargs
            ):
        """
        Creates a new row from a SpinElfLabeler object
        """
        # get structure dict info
        structure_dict = cls._from_toolkit(
            structure=labeler.structure,
            as_dict=True
            )
        
        results = {}
        results["total_labeled_structure"] = labeler.labeled_structure.to_json()
        results["total_quasi_atom_structure"] = labeler.quasi_atom_structure.to_json()
        results["average_atom_elf_radii"] = [float(i) for i in labeler.average_atom_elf_radii]
            
        oxidation_states, charges, volumes = labeler.get_oxidation_and_volumes_from_potcar(
            potcar_path = directory / "POTCAR",
            **kwargs
            )
        results["total_oxidation_states"] = oxidation_states.tolist()
        results["total_charges"] = charges.tolist()
        results["average_volumes"] = volumes.tolist()
        results["differing_spin"] = not labeler._equal_spin
        
        # add setting kwargs
        cutoff_kwargs = {}
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
            cutoff_kwargs[attr] = getattr(labeler, attr, None)
        results["cutoff_kwargs"] = cutoff_kwargs
        
        # create spin up/down entries
        labeler_up = ElfAnalysis.from_labeler(labeler.elf_labeler_up, directory)
        labeler_down = ElfAnalysis.from_labeler(labeler.elf_labeler_down, directory)   

        # create new entry
        new_row = cls(
            analysis_up=labeler_up,
            analysis_down=labeler_down,
            **results,
            **structure_dict
            )
        new_row.save()
        return new_row

            
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

class SpinElfAnalysisCalculation(Calculation):
    """
    This table contains results from a spin-separated ELF topology 
    analysis calculation. The results should be from a dedicated workflow. 
    """
    class Meta:
        app_label = "baderkit"
    
    analysis = table_column.ForeignKey(
        "baderkit.SpinElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="calculation",
        blank=True,
        null=True,
    )
    
    def update_from_spin_labeler(self, labeler: SpinElfLabeler, directory: Path, **kwargs):
        # create an entry in the SpinElfAnalysis table
        labeler = SpinElfAnalysis.from_spin_labeler(labeler, directory)
        # link to table
        self.analysis = labeler
        self.save()


class ElfFeatures(DatabaseTable):
    """
    This table contains the elf features calculated during an elf analysis
    calculation
    """
    class Meta:
        app_label = "baderkit"
    
    analysis = table_column.ForeignKey(
        "baderkit.ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="elf_features",
    )
    
    ###########################################################################
    # Columns for all irreducible domains
    ###########################################################################
    
    domain_subtype = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The type of attractor this domain is, e.g. point, ring, cage
    """
    
    feature_type = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The type of feature this domain was labeled as, e.g. core, shell, covalent bond, etc.
    """
    
    frac_coords = table_column.JSONField(blank=True, null=True)
    """
    The fractional coordinates of the local maxima in this feature. There may
    are often more than one in features such as shells.
    """
    
    average_frac_coords = table_column.JSONField(blank=True, null=True)
    """
    The merged fractional coordinates of the local maxima in this feature.
    """
    
    max_value = table_column.FloatField(blank=True, null=True)
    """
    The maximum elf value that this feature exists at
    """
    
    min_value = table_column.FloatField(blank=True, null=True)
    """
    The minimum elf value that this feature exists at (not inclusive)
    """
    
    depth = table_column.FloatField(blank=True, null=True)
    """
    The depth of this feature defined as the difference in the maximum ELF
    to the ELF value at which the feature bifurcated from a larger domain.
    """
    
    depth_to_infinite = table_column.FloatField(blank=True, null=True)
    """
    The depth of this feature defined as the difference between the
    maximum ELF of the feature to the ELF at which it connects to an
    ELF domain extending infinitely
    """
    
    charge = table_column.FloatField(blank=True, null=True)
    """
    The charge contained in this feature
    """
    
    volume = table_column.FloatField(blank=True, null=True)
    """
    The volume of this feature
    """
    
    nearest_atom = table_column.FloatField(blank=True, null=True)
    """
    The index of the nearest atom to this feature
    """
    
    nearest_atom_species = table_column.CharField(
        blank=True,
        null=True,
        max_length=10,
    )
    """
    The type of atom that is closest to this feature
    """
    
    atom_distance = table_column.FloatField(blank=True, null=True)
    """
    The distance from this feature to the nearest atom
    """
    
    labeled_structure_index = table_column.IntegerField(blank=True, null=True)
    """
    The index of the dummy atom in the labeled structure that this feature belongs
    to
    """
    
    quasi_atom_structure_index = table_column.IntegerField(blank=True, null=True)
    """
    The index of the dummy atom in the quasi atom structure that this feature belongs
    to
    """
    
    min_surface_dist = table_column.FloatField(blank=True, null=True)
    """
    The distance from the average maximum of this feature to the nearest point
    on the partitioning surface.
    """
    
    avg_surface_dist = table_column.FloatField(blank=True, null=True)
    """
    The average distance from the average maximum of this feature to the each
    point on its partitioning surface
    """
    
    
    dist_beyond_atom = table_column.FloatField(blank=True, null=True)
    """
    The distance from this feature to the neighboring atom minus that atoms
    radius determined from the ELF.
    """
    
    coord_number = table_column.IntegerField(blank=True, null=True)
    """
    The coordination number of this feature
    """
    
    coord_atom_indices = table_column.JSONField(blank=True, null=True)
    """
    The structure indices of each of the coordinated atoms
    """
    
    coord_atom_species = table_column.JSONField(blank=True, null=True)
    """
    The symbol of each of the coordinated atoms
    """
    
    quasi_coord_number = table_column.IntegerField(blank=True, null=True)
    """
    The coordination number of this feature including quasi atoms (i.e. electrides)
    """
    
    coord_quasi_atom_indices = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure indices of each of the coordinated atoms in the
    quasi-atom structure
    """
    
    coord_quasi_atom_species = table_column.JSONField(blank=True, null=True)
    """
    The symbol of each of the coordinated atoms in the quasi-atom structure
    """
    