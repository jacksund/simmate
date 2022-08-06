# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.dynamics.base import DynamicsWorkflow
from simmate.calculators.vasp.tasks.dynamics import MITDynamics
from simmate.calculators.vasp.database.dynamics import MITDynamicsRun


class Dynamics__Vasp__Mit(DynamicsWorkflow):
    """
    Run a molecular dynamics simuluation
    """

    description_doc_short = "uses MIT Project settings"
    database_table = MITDynamicsRun
    s3task = MITDynamics
