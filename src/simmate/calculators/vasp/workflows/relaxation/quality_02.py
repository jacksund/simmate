# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality02Relaxation as Quality02RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality02Relaxation as Quality02RelaxationResults,
)


class Quality02Relaxation(Workflow):
    name = "relaxation/quality02"
    project_name = "Simmate-Relaxation"
    s3task = Quality02RelaxationTask
    database_table = Quality02RelaxationResults
    register_kwargs = ["structure", "source"]
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
