# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    Quality04Energy as Quality04EnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    Quality04StaticEnergy as Quality04StaticEnergyResults,
)


class Quality04StaticEnergy(Workflow):
    name = "static-energy/quality04"
    project_name = "Simmate-Energy"
    s3task = Quality04EnergyTask
    database_table = Quality04StaticEnergyResults
    register_kwargs = ["structure", "source"]
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
