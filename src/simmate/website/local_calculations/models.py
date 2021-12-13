# -*- coding: utf-8 -*-

# I store all of my models elsewhere, so this file simply exists to show django where
# they are located at. I do this based on the directions given by:
# https://docs.djangoproject.com/en/3.1/topics/db/models/#organizing-models-in-a-package

from simmate.database.local_calculations.energy import (
    MITStaticEnergy,
    Quality04StaticEnergy,
)

from simmate.database.local_calculations.relaxation import (
    MITRelaxation,
    MITIonicStep,
    Quality00Relaxation,
    Quality00IonicStep,
    Quality01Relaxation,
    Quality01IonicStep,
    Quality02Relaxation,
    Quality02IonicStep,
    Quality03Relaxation,
    Quality03IonicStep,
    Quality04Relaxation,
    Quality04IonicStep,
    StagedRelaxation,
)

from simmate.database.local_calculations.evolution import (
    EvolutionarySearch,
    StructureSource,
)
