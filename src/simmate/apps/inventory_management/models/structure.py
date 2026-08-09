# -*- coding: utf-8 -*-

from simmate.database.mixins import Structure as StructureMixin


class Structure(StructureMixin):
    """
    A crystal structure.

    This table stores the unit cell, atomic sites, and spacegroup information
    for a crystal structure.
    """

    class Meta:
        db_table = "inventory_management__structures"
