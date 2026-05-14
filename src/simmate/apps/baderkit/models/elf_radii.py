# -*- coding: utf-8 -*-

from .base import BaderkitBase
from .elf_radius import AllElfRadii, AtomElfRadii
from simmate.database.base_data_types import table_column


class ElfRadii(BaderkitBase):
    """
    This table contains the elf ionic radii calculated during a badelf calculation
    """
    
    _local_tables = [AllElfRadii, AtomElfRadii]

    class Meta:
        app_label = "baderkit"
