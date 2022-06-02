# -*- coding: utf-8 -*-

"""
Build a workflow in Simmate involves piecing together our Tasks and Database 
tables. So before you start editting this file, make sure you have gone through
and editted the `models.py` and `tasks.py` files. 
"""

# This function is what we use to automatically built simple one-task workflows
from simmate.workflow_engine import s3task_to_workflow

# Import our tables and tasks from the other files.
# Note, the format `import <name> as <newname>` simply renames the class so
# that the table/task classes don't have the same name in this file.
from .models import ExampleRelaxation as ExampleRelaxationTable
from .tasks import ExampleRelaxation as ExampleRelaxationTask

# Now build our workflow
example_workflow = s3task_to_workflow(
    # The naming convention here follows how you would import this workflow.
    # We would do this with `from example_app import example_workflow`, so
    # this import corresponds to the following name:
    name="example_app/example_workflow",
    # This line is always the same and should be left unchanged
    module=__name__,
    # Set the name where you want this to show up in prefect cloud
    project_name="Simmate-Relaxation",
    # Simply set these two variables to your Task and DatabaseTable classes!
    s3task=ExampleRelaxationTable,
    calculation_table=ExampleRelaxationTable,
    # this sets what should be saved to the database BEFORE the calculation
    # is actually started. This helps you search your database for calculations
    # that have not completed yet.
    register_kwargs=["structure", "source"],
    # Quick description that will be used in the website interface
    description_doc_short="This is my new fancy workflow!",
)
