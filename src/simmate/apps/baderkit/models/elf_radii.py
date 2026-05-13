# -*- coding: utf-8 -*-

from .base import BaderkitBase
from .elf_radius import ElfRadius, AtomElfRadius
from simmate.database.base_data_types import table_column


class ElfRadii(BaderkitBase):
    """
    This table contains the elf ionic radii calculated during a badelf calculation
    """
    
    _local_tables = [ElfRadius, AtomElfRadius]

    class Meta:
        app_label = "baderkit"

    site_index = table_column.IntegerField()
    """
    The index of the central atom that the radius is for
    """
    neigh_index = table_column.IntegerField()
    """
    The index of the neighboring atom
    """
    radius = table_column.FloatField()
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
    radius_type = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The type of radius, i.e. covalent or ionic
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