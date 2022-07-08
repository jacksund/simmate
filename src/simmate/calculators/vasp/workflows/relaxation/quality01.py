# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality01Relaxation as Quality01RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality01Relaxation as Quality01RelaxationResults,
)


class Relaxation__Vasp__Quality01(Workflow):
    s3task = Quality01RelaxationTask
    database_table = Quality01RelaxationResults
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
