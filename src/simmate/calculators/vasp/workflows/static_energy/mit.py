# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    MITStaticEnergy as MITStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    MITStaticEnergy as MITStaticEnergyResults,
)


class StaticEnergy__Vasp__Mit(Workflow):
    s3task = MITStaticEnergyTask
    database_table = MITStaticEnergyResults
    description_doc_short = "uses MIT Project settings"
