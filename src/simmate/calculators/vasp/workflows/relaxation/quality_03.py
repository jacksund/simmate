# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality03Relaxation as Quality03RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality03Relaxation as Quality03RelaxationResults,
)


class Quality03Relaxation(Workflow):
    name = "relaxation/quality03"
    project_name = "Simmate-Relaxation"
    s3task = Quality03RelaxationTask
    database_table = Quality03RelaxationResults
    register_kwargs = ["structure", "source"]
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
