# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    MatprojSCANStaticEnergy as MPStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    MatprojSCANStaticEnergy as MPStaticEnergyResults,
)


class StaticEnergy__Vasp__MatprojScan(Workflow):
    s3task = MPStaticEnergyTask
    database_table = MPStaticEnergyResults
    description_doc_short = "uses Materials Project SCAN settings"
