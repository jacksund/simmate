# -*- coding: utf-8 -*-

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

from .tasks.supervised_staged_shell_task import S3Task
from .tasks.workflow_task import WorkflowTask
from .workflow import Workflow, Parameter, ModuleStorage
from .error_handler import ErrorHandler

# from .utilities import s3task_to_workflow  # NOT MODULAR - REQUIRES DB CONNECTION
