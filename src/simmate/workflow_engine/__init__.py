# -*- coding: utf-8 -*-

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

# OPTIMIZE: These imports are particularly slow because we are configuring
# django in the code below this. These two imports don't depend on the database
# module, so it may be worth isolating them for faster imports.
from .error_handler import ErrorHandler
from .supervised_staged_shell_task import S3Task
from .worker import Worker

# All imports below this point depend on the simmate.database module and therefore
# need a database connection. This line sets up the database connection so
# that models can be imported.
from simmate.database import connect

from .workflow import Workflow, task
