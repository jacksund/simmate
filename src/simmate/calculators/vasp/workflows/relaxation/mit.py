# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MITRelaxation as MITRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MITRelaxation as MITRelaxationResults,
)


class Relaxation__Vasp__Mit(Workflow):
    s3task = MITRelaxationTask
    database_table = MITRelaxationResults
    description_doc_short = "uses MIT Project settings"
