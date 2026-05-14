# -*- coding: utf-8 -*-


from simmate.database.base_data_types import table_column
from .base import BaderkitLocalBase


class AllElfRadii(BaderkitLocalBase):
    """
    This table contains the elf ionic radii calculated during a badelf calculation
    """
    
    range_attribute = "site_indices"

    class Meta:
        app_label = "baderkit"

    site_indices = table_column.IntegerField()
    """
    The index of the central atom that the radius is for
    """
    neigh_indices = table_column.IntegerField()
    """
    The index of the neighboring atom
    """
    all_radii = table_column.FloatField()
    """
    The ELF ionic radius between the central atom and neighbor atom
    """
    site_frac_coords = table_column.JSONField()
    """
    The fractional coordinates of the first site
    """
    neigh_frac_coords = table_column.JSONField()
    """
    The fractional coordinates of the second site
    """
    all_bond_types = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The type of radius, i.e. ionic, covalent, metallic, or non-bonding
    """
    spin_system = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The electron spin system this radius was calculated from. Options
    are:
        up - spin-up
        down - spin-down
        not polarized - calculation not spin polarized
    """
    
    elf_radii = table_column.ForeignKey(
        "baderkit.ElfRadii",
        on_delete=table_column.CASCADE,
        related_name="%(class)s",
    )
    
class AtomElfRadii(BaderkitLocalBase):
    """
    This table contains the elf ionic radii calculated during a badelf calculation
    """
    
    range_attribute = "atom_radii"

    class Meta:
        app_label = "baderkit"

    atom_radii = table_column.FloatField()
    """
    The ELF ionic radius between the central atom and neighbor atom
    """
    
    atom_bond_types = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The type of radius, i.e. ionic, covalent, metallic, or non-bonding
    """
    
    species = table_column.JSONField(blank=True, null=True)
    """
    The species this radius belongs to
    """
    
    elf_radii = table_column.ForeignKey(
        "baderkit.ElfRadii",
        on_delete=table_column.CASCADE,
        related_name="%(class)s",
    )
    