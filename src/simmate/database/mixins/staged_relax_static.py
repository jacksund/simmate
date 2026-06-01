# -*- coding: utf-8 -*-

from ..core import table_column
from .forces import Forces
from .staged import StagedWorkflow
from .structure import Structure
from .thermodynamics import Thermodynamics


class StagedRelaxStatic(StagedWorkflow, Structure, Thermodynamics, Forces):
    class Meta:
        app_label = "workflow_explorer"
        db_table = "workflows_stagedrelaxstatic"
