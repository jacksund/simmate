# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.dynamics.base import DynamicsWorkflow
from simmate.calculators.vasp.tasks.dynamics import MatVirtualLabNPTDynamics
from simmate.calculators.vasp.database.dynamics import MatVirtualLabNPTDynamicsRun


class Dynamics__Vasp__MvlNpt(DynamicsWorkflow):
    """
    Run a molecular dynamics simuluation
    """

    description_doc_short = "uses MIT Project settings"
    database_table = MatVirtualLabNPTDynamicsRun
    s3task = MatVirtualLabNPTDynamics
