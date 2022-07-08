# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.density_of_states import (
    MatprojDensityOfStates as MatprojDensityOfStatesTask,
)
from simmate.calculators.vasp.database.density_of_states import (
    MatprojDensityOfStates as MatprojDensityOfStatesResults,
)


class ElectronicStructure__Vasp__MatprojDensityOfStates(Workflow):
    s3task = MatprojDensityOfStatesTask
    database_table = MatprojDensityOfStatesResults
    description_doc_short = "uses Materials Project settings (PBE)"
