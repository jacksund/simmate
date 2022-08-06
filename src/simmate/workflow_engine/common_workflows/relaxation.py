# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.database.base_data_types import Relaxation


class RelaxationWorkflow(Workflow):
    database_table = Relaxation
