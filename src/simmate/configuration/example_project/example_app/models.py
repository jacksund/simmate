# -*- coding: utf-8 -*-

"""
This is where you add any new database tables you'd like. This file is named
"models.py" because that what Django expects! In their terminology, a django 
model is the same thing as a database table.

As an example here,we set up tables for a VASP relaxation. There are two tables
here: one for the relaxations and a second for storing each ionic step in the 
relaxation.

Note that we use IonicStepStructure and Relaxation classes to inherit from.
This let's us automatically add useful columns and features -- so you don't have
to add everything from scratch. The only code that we write here simply connects
these database tables and/or adds new custom columns.
"""

from simmate.database.base_data_types import table_column

from simmate.database.local_calculations.relaxation.base import (
    IonicStepStructure,
    Relaxation,
)

# All ionic steps of relaxations are stored in the same table. This means the
# start structure, end structure, and those structure in-between are stored
# together here.


class MITRelaxationStructure(IonicStepStructure):

    # All structures in this table come from relaxation calculations, where
    # there can be many structures (one for each ionic steps) linked to a
    # single relaxation
    relaxation = table_column.ForeignKey(
        "MITRelaxation",  # in quotes becuase this is defined below
        on_delete=table_column.CASCADE,
        related_name="structures",
    )


class MITRelaxation(Relaxation):

    """Base Info"""

    # All the base information is contained with the parent classes

    """ Relationships """
    # the source structure for this calculation
    structure_start = table_column.OneToOneField(
        MITRelaxationStructure,
        on_delete=table_column.CASCADE,
        related_name="relaxations_as_start",
        blank=True,
        null=True,
    )

    # the final structure for this calculation
    structure_final = table_column.OneToOneField(
        MITRelaxationStructure,
        on_delete=table_column.CASCADE,
        related_name="relaxations_as_final",
        blank=True,
        null=True,
    )

    # all other structures are accessible through the "structures" field
