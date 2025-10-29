# -*- coding: utf-8 -*-

from simmate.database.base_data_types import (
    DatabaseTable,
    table_column,
)

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
    