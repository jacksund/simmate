# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality03Relaxation as Quality03RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality03Relaxation as Quality03RelaxationResults,
)


class Relaxation__Vasp__Quality03(Workflow):
    s3task = Quality03RelaxationTask
    database_table = Quality03RelaxationResults
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
