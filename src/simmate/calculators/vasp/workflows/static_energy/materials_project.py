# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    MatProjStaticEnergy as MPStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    MatProjStaticEnergy as MPStaticEnergyResults,
)


class MatProjStaticEnergy(Workflow):
    name = "static-energy/matproj"
    project_name = "Simmate-Energy"
    s3task = MPStaticEnergyTask
    database_table = MPStaticEnergyResults
    register_kwargs = ["structure", "source"]
    description_doc_short = "uses Materials Project settings"
