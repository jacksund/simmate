# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality00Relaxation as Quality00RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality00Relaxation as Quality00RelaxationResults,
)


class Quality00Relaxation(Workflow):
    name = "relaxation/quality00"
    project_name = "Simmate-Relaxation"
    s3task = Quality00RelaxationTask
    database_table = Quality00RelaxationResults
    register_kwargs = ["structure", "source"]
    description_doc_short = "bare minimum settings meant for highly unreasonable structures. lattice volume kept fixed"
