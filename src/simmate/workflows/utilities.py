# -*- coding: utf-8 -*-

from simmate import workflows
from simmate.workflow_engine.workflow import Workflow
from simmate.workflow_engine.tasks.supervised_staged_shell_task import S3Task


def get_list_of_all_workflows():
    """
    Returns a list of all the workflows located in the workflows module
    """

    # This loop goes through all attributes (as strings) of the workflow module
    # and select only those that are workflow or s3tasks.
    workflow_names = []
    for attr_name in dir(workflows):
        attr = getattr(workflows, attr_name)
        if isinstance(attr, Workflow) or isinstance(attr, S3Task):
            workflow_names.append(attr_name)
    # OPTIMIZE: is there a more efficient way to do this?

    return workflow_names
