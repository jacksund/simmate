# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MatprojRelaxation as MPRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MatprojRelaxation as MPRelaxationResults,
)


class Relaxation__Vasp__Matproj(Workflow):
    s3task = MPRelaxationTask
    database_table = MPRelaxationResults
    description_doc_short = "uses Materials Project settings"
