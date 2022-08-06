# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.dynamics.base import DynamicsWorkflow
from simmate.calculators.vasp.tasks.dynamics import MatprojDynamics
from simmate.calculators.vasp.database.dynamics import MatprojDynamicsRun


class Dynamics__Vasp__Matproj(DynamicsWorkflow):
    """
    Run a molecular dynamics simuluation
    """

    description_doc_short = "uses MIT Project settings"
    database_table = MatprojDynamicsRun
    s3task = MatprojDynamics
