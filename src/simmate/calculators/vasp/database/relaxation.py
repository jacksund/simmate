# -*- coding: utf-8 -*-

"""

We got rid of the boilerplate code! The create_all_subclasses() function below
now does all the work for us. It may be tricky to understand what's happening
behind the scenes, so here's an example:
    
These two lines...
    
    from simmate.database.local_calculations.relaxation.base import Relaxation

    ExampleRelaxation, ExampleIonicStep = Relaxation.create_all_subclasses("Example", module=__name__)



Do exactly the same thing as all of these lines...

    from simmate.database.base_data_types import table_column
    from simmate.database.local_calculations.relaxation.base import (
        IonicStep,
        Relaxation,
    )
    
    class ExampleIonicStep(IonicStep):
        relaxation = table_column.ForeignKey(
            "ExampleRelaxation",  # in quotes becuase this is defined below
            on_delete=table_column.CASCADE,
            related_name="structures",
        )
    
    class ExampleRelaxation(Relaxation):
        structure_start = table_column.OneToOneField(
            ExampleIonicStep,
            on_delete=table_column.CASCADE,
            related_name="relaxations_as_start",
            blank=True,
            null=True,
        )
        structure_final = table_column.OneToOneField(
            ExampleIonicStep,
            on_delete=table_column.CASCADE,
            related_name="relaxations_as_final",
            blank=True,
            null=True,
        )

"""

from simmate.database.base_data_types.calculation import NestedCalculation
from simmate.database.base_data_types.relaxation import Relaxation

# Between all of the different relaxations that simmate runs, there's no
# difference between any of the datatables we store results in. The difference
# is only HOW the relaxation was ran, which is why we store them in separate
# tables.

MITRelaxation, MITIonicStep = Relaxation.create_all_subclasses("MIT", module=__name__)

Quality00Relaxation, Quality00IonicStep = Relaxation.create_all_subclasses(
    "Quality00",
    module=__name__,
)

Quality01Relaxation, Quality01IonicStep = Relaxation.create_all_subclasses(
    "Quality01",
    module=__name__,
)

Quality02Relaxation, Quality02IonicStep = Relaxation.create_all_subclasses(
    "Quality02",
    module=__name__,
)

Quality03Relaxation, Quality03IonicStep = Relaxation.create_all_subclasses(
    "Quality03",
    module=__name__,
)

Quality04Relaxation, Quality04IonicStep = Relaxation.create_all_subclasses(
    "Quality04",
    module=__name__,
)

StagedRelaxation = NestedCalculation.create_subclass_from_calcs(
    "StagedRelaxation",
    [
        Quality00Relaxation,
        Quality01Relaxation,
        Quality02Relaxation,
        Quality03Relaxation,
        Quality04Relaxation,
    ],
    module=__name__,
)
