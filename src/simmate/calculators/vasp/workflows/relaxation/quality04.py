# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality04Relaxation as Quality04RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality04Relaxation as Quality04RelaxationResults,
)


class Relaxation__Vasp__Quality04(Workflow):
    s3task = Quality04RelaxationTask
    database_table = Quality04RelaxationResults
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
