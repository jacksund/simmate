# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.density_of_states import (
    MatProjDensityOfStates as MatProjDensityOfStatesTask,
)
from simmate.calculators.vasp.database.density_of_states import (
    MatProjDensityOfStates as MatProjDensityOfStatesResults,
)


class ElectronicStructure__Vasp__MatProjDensityOfStates(Workflow):
    s3task = MatProjDensityOfStatesTask
    database_table = MatProjDensityOfStatesResults
    register_kwargs = ["structure", "source"]
    description_doc_short = "uses Materials Project settings (PBE)"
