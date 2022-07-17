# -*- coding: utf-8 -*-

"""
Build a workflow in Simmate involves piecing together our Tasks and Database 
tables. So before you start editting this file, make sure you have gone through
and editted the `models.py` and `tasks.py` files.

This is the most basic Workflow that you may build. For complex workflows that
require several calculations, other python logic, and parallelization, make
sure you read through the documentation for 
[the Workflow class](https://jacksund.github.io/simmate/simmate/workflow_engine/workflow.html)
"""

# To access advanced functionality, we should always inherit from the base Workflow
from simmate.workflow_engine import Workflow

# Import our tables and tasks from the other files.
# Note, the format `from <place> import <name> as <newname>` simply renames the class so
# that the table/task classes don't have the same name in this file.
from .models import ExampleRelaxation as ExampleRelaxationTable
from .tasks import ExampleRelaxation as ExampleRelaxationTask

# Now build our workflow
class Relaxation__Vasp__MyCustomSettings(Workflow):
    # Simply set these two variables to your Task and DatabaseTable classes!
    s3task = ExampleRelaxationTask
    database_table = ExampleRelaxationTable
