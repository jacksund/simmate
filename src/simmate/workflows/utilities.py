# -*- coding: utf-8 -*-

from simmate.workflows import all as all_workflows


def get_list_of_all_workflows():
    """
    Returns a list of all the workflows located in the workflows.all module
    """

    workflow_names = [n for n in dir(all_workflows) if "__" not in n]
    return workflow_names
