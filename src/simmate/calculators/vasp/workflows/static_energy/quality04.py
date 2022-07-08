# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    Quality04Energy as Quality04EnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    Quality04StaticEnergy as Quality04StaticEnergyResults,
)


class StaticEnergy__Vasp__Quality04(Workflow):
    s3task = Quality04EnergyTask
    database_table = Quality04StaticEnergyResults
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
