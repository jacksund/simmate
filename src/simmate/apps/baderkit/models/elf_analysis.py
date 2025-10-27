# -*- coding: utf-8 -*-

from pathlib import Path

from baderkit.core import ElfLabeler, SpinElfLabeler

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Structure,
    table_column,
)

class SpinElfAnalysis(Structure, Calculation):
    """
    This table contains results from a spin-dependant ELF topology analysis
    """
    cutoff_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used when labeling features in the structure
    """
    
    elf_analysis_up = table_column.ForeignKey(
        "ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="spin_elf_analysis",
    )
    
    elf_analysis_down = table_column.ForeignKey(
        "ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="spin_elf_analysis",
    )
    
    labeled_structure = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure with dummy atoms representing the location of chemical
    features in the system. This is a combination of the dummy atoms found in
    both the spin up and spin down systems.
    """

    quasi_atom_structure = table_column.JSONField(blank=True, null=True)
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
    
    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states for each quasi atom.
    """

    atomic_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each quasi atom.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """
    
    atomic_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of quasi atom volumes from the oxidation analysis (i.e. the bader volume)
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
    
    def update_from_spin_labeler(
            self, 
            labeler: SpinElfLabeler,
            directory: Path,
            **kwargs
            ):
        """
        Creates a new row from a SpinElfLabeler object
        """
        results = {}
        results["structure"] = labeler.structure
        results["labeled_structure"] = labeler.labeled_structure.to_json()
        results["quasi_atom_structure"] = labeler.quasi_atom_structure.to_json()
        results["average_atom_elf_radii"] = [float(i) for i in labeler.average_atom_elf_radii]
            
        oxidation_states, charges, volumes = labeler.get_oxidation_and_volumes_from_potcar(
            potcar_path = directory / "POTCAR",
            **kwargs
            )
        results["oxidation_states"] = oxidation_states
        results["atomic_charges"] = charges
        results["atomic_volumes"] = volumes
        
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
        new_row = SpinElfAnalysis(**results)
        new_row.save()
        # update spin up/down labelers
        labeler_up_model = self.elf_analysis_up.model
        labeler_up_model.update_from_labeler(labeler.elf_labeler_up)
        
        labeler_down_model = self.elf_analysis_down.model
        labeler_down_model.update_from_labeler(labeler.elf_labeler_down)
        


class ElfAnalysis(Structure, Calculation):
    """
    This table contains results from an ELF topology analysis.
    """
    
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

    atomic_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each quasi atom.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """
    
    atomic_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of quasi atom volumes from the oxidation analysis (i.e. the bader volume)
    """
    
    spin_system = table_column.CharField(
        blank=True,
        null=True,
        max_length=25,
    )
    """
    Which type of spin this calculation was performed on i.e. up, down, or total
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
    
    def update_from_labeler(
            self, 
            labeler: ElfLabeler,
            directory: Path,
            **kwargs
            ):
        """
        Creates a new row from an ElfLabeler object
        """
        results = {}
        results["structure"] = labeler.structure
        results["bifurcation_graph"] = labeler.bifurcation_graph.to_json()
        results["labeled_structure"] = labeler.labeled_structure.to_json()
        results["quasi_atom_structure"] = labeler.quasi_atom_structure.to_json()
        results["atom_elf_radii"] = [float(i) for i in labeler.atom_elf_radii]
        results["quasi_atom_elf_radii"] = [float(i) for i in labeler.quasi_atom_elf_radii]
            
        oxidation_states, charges, volumes = labeler.get_oxidation_and_volumes_from_potcar(
            potcar_path = directory / "POTCAR",
            **kwargs
            )
        results["oxidation_states"] = oxidation_states
        results["atomic_charges"] = charges
        results["atomic_volumes"] = volumes
        
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
        new_row = ElfAnalysis(**results)
        new_row.save()
        # update elf features
        self.update_elf_features(labeler)

    def update_elf_features(self, labeler: ElfLabeler):
        # pull all the data together and save it to the database. We
        # are saving this to an ElfIonicRadii datatable. To access this
        # model, we need to use "elf_features.model".
        feature_model = self.elf_features.model
        # Let's iterate through the ELF features and save these to the database.
        for node in labeler.bifurcation_graph.irreducible_nodes:
            # get dict of all info for this feature
            new_row_dict = {}
            for entry in feature_model.columns:
                new_row_dict[entry] = getattr(node, entry, None)
            # update values not stored directly in dict
            new_row_dict["elf_analysis"] = self
            new_row = feature_model(**new_row_dict)
            new_row.save()

class ElfFeatures(DatabaseTable):
    """
    This table contains the elf features calculated during an elf analysis
    calculation
    """
    elf_analysis = table_column.ForeignKey(
        "ElfAnalysis",
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
    
    nearest_atom_type = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The type of atom that is closest to this feature
    """
    
    atom_distance = table_column.FloatField(blank=True, null=True)
    """
    The distance from this feature to the nearest atom
    """
    
    quasi_atom_structure_index = table_column.IntegerField(blank=True, null=True)
    """
    The index of the dummy atom in the labeled structure that this feature belongs
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
    