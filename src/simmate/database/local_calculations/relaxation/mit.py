# -*- coding: utf-8 -*-

"""

We got rid of the boilerplate code! The create_all_subclasses() function below
now does all the work for us. It may be tricky to understand what's happening
behind the scenes, so here's an example. This code does the exact same thing
as Relaxation.create_all_subclasses("MIT")!


from simmate.database.base_data_types import table_column
from simmate.database.local_calculations.relaxation.base import (
    IonicStep,
    Relaxation,
)

class MITIonicStep(IonicStep):
    relaxation = table_column.ForeignKey(
        "MITRelaxation",  # in quotes becuase this is defined below
        on_delete=table_column.CASCADE,
        related_name="structures",
    )

class MITRelaxation(Relaxation):
    structure_start = table_column.OneToOneField(
        MITIonicStep,
        on_delete=table_column.CASCADE,
        related_name="relaxations_as_start",
        blank=True,
        null=True,
    )
    structure_final = table_column.OneToOneField(
        MITIonicStep,
        on_delete=table_column.CASCADE,
        related_name="relaxations_as_final",
        blank=True,
        null=True,
    )
"""


from simmate.database.local_calculations.relaxation.base import Relaxation

MITRelaxation, MITIonicStep = Relaxation.create_all_subclasses("MIT")
