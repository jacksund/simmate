# -*- coding: utf-8 -*-

# The order that we import these different modules is important to prevent
# circular imports errors, so we prevent isort from changing this file.
# isort: skip_file

from simmate.utilities import get_doc_from_readme

__doc__ = get_doc_from_readme(__file__)

# OPTIMIZE: These imports are particularly slow because we are configuring
# django in the code below this. These two imports don't depend on the database
# module, so it may be worth isolating them for faster imports.
from .error_handler import ErrorHandler

# All imports below this point depend on the simmate.database module and therefore
# need a database connection. This line sets up the database connection so
# that models can be imported.
from simmate.database import connect


from .workflow import Workflow
from .s3_workflow import S3Workflow
from .execution import SimmateWorker as Worker
