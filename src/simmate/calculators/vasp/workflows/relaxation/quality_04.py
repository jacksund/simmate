# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality04Relaxation as Quality04RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality04Relaxation as Quality04RelaxationResults,
)


class Quality03Relaxation(Workflow):
    name = "relaxation/quality04"
    project_name = "Simmate-Relaxation"
    s3task = Quality04RelaxationTask
    database_table = Quality04RelaxationResults
    register_kwargs = ["structure", "source"]
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
