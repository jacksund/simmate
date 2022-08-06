# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.density_of_states import (
    MatprojHSEDensityOfStates as MatprojDensityOfStatesTask,
)
from simmate.calculators.vasp.database.density_of_states import (
    MatprojHSEDensityOfStates as MatprojDensityOfStatesResults,
)


class ElectronicStructure__Vasp__MatprojDensityOfStatesHse(Workflow):
    s3task = MatprojDensityOfStatesTask
    database_table = MatprojDensityOfStatesResults
    description_doc_short = "uses Materials Project settings (HSE)"
