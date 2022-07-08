# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality00Relaxation as Quality00RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality00Relaxation as Quality00RelaxationResults,
)


class Relaxation__Vasp__Quality00(Workflow):
    s3task = Quality00RelaxationTask
    database_table = Quality00RelaxationResults
    description_doc_short = "bare minimum settings meant for highly unreasonable structures. lattice volume kept fixed"
