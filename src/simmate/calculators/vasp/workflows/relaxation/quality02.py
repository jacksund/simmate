# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality02Relaxation as Quality02RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality02Relaxation as Quality02RelaxationResults,
)


class Relaxation__Vasp__Quality02(Workflow):
    s3task = Quality02RelaxationTask
    database_table = Quality02RelaxationResults
    description_doc_short = (
        "low-quality settings meant for highly unreasonable structures"
    )
