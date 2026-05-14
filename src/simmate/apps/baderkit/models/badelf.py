# -*- coding: utf-8 -*-

from .base import BaderkitBase
from simmate.database.base_data_types import table_column


class Badelf(BaderkitBase):
    """
    This table contains results from a BadELF analysis.
    """
    
    class Meta:
        app_label = "baderkit"

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    The oxidation states for each atom and electride in the system.
    """

    nna_structure = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure with dummy atoms representing the location of quasi
    atoms (e.g. electrides, bare electrons, etc.)
    """

    atom_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each atom and electride
    feature in the system (i.e. electride/covelent bond etc.)
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    atom_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of atom or electride volumes from the oxidation analysis
    """

    min_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an atom or electride 
    to the bader/plane surface.
    """

    avg_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    A list of average distances from the origin of an atom or electride 
    to the bader/plane surface.
    """

    maxima_elf_values = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima for each atom and electride in the system.
    """

    nna_formula = table_column.CharField(
        blank=True,
        null=True,
        max_length=25,
    )
    """
    The approximate formula for the structure including quasi-atoms (e.g. 
    electrides, multi-centered bonds, etc.)
    The value is rounded to the nearest integer.
    """

    nnas_per_formula = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons assigned to electride sites for this structures
    formula unit.
    """

    nnas_per_reduced_formula = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons assigned to electride sites for this structures
    reduced formula unit.
    """

    num_nnas = table_column.IntegerField(blank=True, null=True)
    """
    The total number of electrides that were found when searching the maxima
    found using pybader.
    """

    nna_dimensionality = table_column.IntegerField(blank=True, null=True)
    """
    The dimensionality of the electride network in the structure.
    """

    all_nna_dims = table_column.JSONField(blank=True, null=True)
    """
    All dimensionalities the electride network has at varying ELF values
    in the system.
    """

    all_nna_dim_cutoffs = table_column.JSONField(blank=True, null=True)
    """
    The ELF values at which the bare electron volume reduces dimensionality.
    """
    
    total_electron_number = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons involved in the charge density partitioning.
    The value should match the total valence electrons used.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

