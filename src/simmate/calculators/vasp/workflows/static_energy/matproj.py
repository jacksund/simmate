# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    MatprojStaticEnergy as MPStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    MatprojStaticEnergy as MPStaticEnergyResults,
)


class StaticEnergy__Vasp__Matproj(Workflow):
    s3task = MPStaticEnergyTask
    database_table = MPStaticEnergyResults
    description_doc_short = "uses Materials Project settings"
