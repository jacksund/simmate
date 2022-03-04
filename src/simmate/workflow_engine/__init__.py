# -*- coding: utf-8 -*-

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

# OPTIMIZE: These imports are particularly slow because we are configuring
# django in the code below this. These two imports don't depend on the database
# module, so it may be worth isolating them for faster imports.
from .error_handler import ErrorHandler
from .supervised_staged_shell_task import S3Task

# All imports below this point depend on the simmate.database module and therefore
# need a database connection. This line sets up the database connection so
# that models can be imported.
from simmate.configuration.django import setup_full  # sets database connection

from .workflow_task import WorkflowTask
from .workflow import Workflow, Parameter, ModuleStorage
from .utilities import s3task_to_workflow
