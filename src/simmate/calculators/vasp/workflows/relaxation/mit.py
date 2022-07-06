# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MITRelaxation as MITRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MITRelaxation as MITRelaxationResults,
)


class MITRelaxation(Workflow):
    name = "relaxation/mit"
    project_name = "Simmate-Relaxation"
    s3task = MITRelaxationTask
    database_table = MITRelaxationResults
    register_kwargs = ["structure", "source"]
    description_doc_short = "uses MIT Project settings"
