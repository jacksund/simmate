# -*- coding: utf-8 -*-

from .staged import StagedWorkflow


class StagedRelaxStatic(StagedWorkflow):
    use_database = True
