# -*- coding: utf-8 -*-

"""
This module creates all database tables for vasp relaxation workflows.

With the exception of StagedRelaxation, the data stored in each table is exactly 
the same -- so they all inherit from the `Relaxation` class without adding any
features. See `simmate.database.base_data_types.relaxation` for details.

StagedRelaxation on the other hand is a NestedCalculation -- in that it connects
a series of relaxation. See `simmate.database.base_data_types.calculation_nested`
for details.
"""

from simmate.database.base_data_types import Relaxation, NestedCalculation

# Between all of the different relaxations that simmate runs, there's no
# difference between any of the datatables we store results in. The difference
# is only HOW the relaxation was ran (i.e. the VASP settings used), which is
# why we store them in separate tables.

MITRelaxation, MITIonicStep = Relaxation.create_subclasses("MIT", module=__name__)

(
    MatProjRelaxation,
    MatProjIonicStep,
) = Relaxation.create_subclasses("MatProj", module=__name__)

NEBEndpointRelaxation, NEBEndpointIonicStep = Relaxation.create_subclasses(
    "NEBEndpoint",
    module=__name__,
)

Quality00Relaxation, Quality00IonicStep = Relaxation.create_subclasses(
    "Quality00",
    module=__name__,
)

Quality01Relaxation, Quality01IonicStep = Relaxation.create_subclasses(
    "Quality01",
    module=__name__,
)

Quality02Relaxation, Quality02IonicStep = Relaxation.create_subclasses(
    "Quality02",
    module=__name__,
)

Quality03Relaxation, Quality03IonicStep = Relaxation.create_subclasses(
    "Quality03",
    module=__name__,
)

Quality04Relaxation, Quality04IonicStep = Relaxation.create_subclasses(
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
