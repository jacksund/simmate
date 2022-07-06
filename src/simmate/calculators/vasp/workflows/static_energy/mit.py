# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    MITStaticEnergy as MITStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    MITStaticEnergy as MITStaticEnergyResults,
)


class Static_Energy__VASP__MIT(Workflow):
    s3task = MITStaticEnergyTask
    database_table = MITStaticEnergyResults
    register_kwargs = ["structure", "source"]
    description_doc_short = "uses MIT Project settings"
