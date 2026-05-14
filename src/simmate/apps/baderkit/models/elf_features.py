# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column
from .base import BaderkitLocalBase


class ElfFeatures(BaderkitLocalBase):
    """
    This table contains the elf features calculated during an elf analysis
    calculation
    """
    
    range_attribute = "basin_types"

    class Meta:
        app_label = "baderkit"

    basin_types = table_column.JSONField(blank=True, null=True)
    """
    The type of chemical feature each basin is a part of.
    """

    basin_charges = table_column.JSONField(blank=True, null=True)
    """
    The charge in each ELF basin
    """

    basin_volumes = table_column.JSONField(blank=True, null=True)
    """
    The volume of each ELF basin
    """
    
    maxima_frac = table_column.JSONField(blank=True, null=True)
    """
    The fractional coordinates of the maxima of each basin
    """
    
    maxima_center_frac = table_column.JSONField(blank=True, null=True)
    """
    The fractional coordinates of the "center of mass" for each maximum in
    the localization function grid. This is used when determining if a basin
    is along a bond, and is particularly necessary for ring shaped covalent bonds.
    """
    
    maxima_elf_values = table_column.JSONField(blank=True, null=True)
    """
    The ELF value at each basins maximum
    """

    attractor_shapes = table_column.JSONField(blank=True, null=True)
    """
    The shape of the attractor (maximum) in the ELF
    """
    
    attractor_depths = table_column.JSONField(blank=True, null=True)
    """
    Difference in value from the maximum to the first value an attractor
    connects to another.
    """
    
    nearest_atoms = table_column.JSONField(blank=True, null=True)
    """
    The closest atom to each basin measured from the center of mass.
    """
    
    nearest_atom_species = table_column.JSONField(blank=True, null=True)
    """
    The type of atom to each basin measured from the center of mass.
    """
    
    heavily_polarized = table_column.JSONField(blank=True, null=True)
    """
    A boolean array representing which ELF basins are considered heavily
    polarized towards an atom. The results depend on the 'polarization_cutoff'
    parameter.
    """
    
    basin_atom_dists = table_column.JSONField(blank=True, null=True)
    """
    The closest atom to each basin measured from the center of mass.
    """
    
    basin_dists_beyond_atoms = table_column.JSONField(blank=True, null=True)
    """
    The distance from each basin's maximum to the site it is assigned to
    """
    
    elf_labeler = table_column.ForeignKey(
        "baderkit.ElfLabeler",
        on_delete=table_column.CASCADE,
        related_name="%(class)s",
    )
