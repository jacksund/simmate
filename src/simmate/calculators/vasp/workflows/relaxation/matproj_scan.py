# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MatprojSCANRelaxation as MPRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MatprojSCANRelaxation as MPRelaxationResults,
)


class Relaxation__Vasp__MatprojScan(Workflow):
    s3task = MPRelaxationTask
    database_table = MPRelaxationResults
    description_doc_short = "uses Materials Project SCAN settings"
