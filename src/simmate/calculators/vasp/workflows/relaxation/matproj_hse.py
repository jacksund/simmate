# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MatprojHSERelaxation as MPRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MatprojHSERelaxation as MPRelaxationResults,
)


class Relaxation__Vasp__MatprojHse(Workflow):
    s3task = MPRelaxationTask
    database_table = MPRelaxationResults
    description_doc_short = "uses Materials Project HSE settings"
