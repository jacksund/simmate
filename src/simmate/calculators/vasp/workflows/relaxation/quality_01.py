# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality01Relaxation as Quality01RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality01Relaxation as Quality01RelaxationResults,
)


class Relaxation__VASP__Quality01(Workflow):
    s3task = Quality01RelaxationTask
    database_table = Quality01RelaxationResults
    register_kwargs = ["structure", "source"]
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
