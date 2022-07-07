# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MatProjRelaxation as MPRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MatProjRelaxation as MPRelaxationResults,
)


class Relaxation__Vasp__MatProj(Workflow):
    s3task = MPRelaxationTask
    database_table = MPRelaxationResults
    register_kwargs = ["structure", "source"]
    description_doc_short = "uses Materials Project settings"
