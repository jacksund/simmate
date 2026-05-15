# -*- coding: utf-8 -*-

from .base import BaderkitBase
from .elf_features import ElfFeatures
from simmate.database.core import table_column


class ElfLabeler(BaderkitBase):
    """
    This table contains data from an ELF topology analysis. It intentionally
    does not inherit from the Calculation table as the results may not
    be generated from a dedicated workflow.
    """
    
    _local_tables = [ElfFeatures]

    class Meta:
        app_label = "baderkit"

    method_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used when labeling features in the structure
    """
    
    max_nna_dist = table_column.FloatField(blank=True, null=True)
    """
    The maximum distance that any NNA in the system sits from its
    neighboring atoms.
    """

    nna_indices = table_column.JSONField(blank=True, null=True)
    """
    The indices of the basins assigned as nnas.
    """

    nna_formula = table_column.CharField(
        blank=True,
        null=True,
        max_length=25,
    )
    """
    The approximate formula for the structure including the electrides.
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
