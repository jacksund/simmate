# -*- coding: utf-8 -*-

from importlib import import_module

from simmate.workflow_engine import Workflow, S3Task


ALL_WORKFLOW_TYPES = [
    "static_energy",
    "relaxation",
    "population_analysis",
    "band_structure",
    "density_of_states",
    "dynamics",
    "diffusion",
]


def get_list_of_workflows_by_type(flow_type: str):
    """
    Returns a list of all the workflows located in the given module
    """

    # Make sure the type is supported
    if flow_type not in ALL_WORKFLOW_TYPES:
        raise TypeError(
            f"{flow_type} is not allowed. Please use a workflow type from this"
            f" list: {ALL_WORKFLOW_TYPES}"
        )

    # grab the relevent module
    flow_module = import_module(f"simmate.workflows.{flow_type}")

    # This loop goes through all attributes (as strings) of the workflow module
    # and select only those that are workflow or s3tasks.
    workflow_names = []
    for attr_name in dir(flow_module):
        attr = getattr(flow_module, attr_name)
        if isinstance(attr, Workflow) or isinstance(attr, S3Task):
            # We remove the _workflow ending for each because it's repetitve.
            # We also change the name from "flow_name" to "flow-name".
            workflow_names.append(attr_name.removesuffix("_workflow").replace("_", "-"))
    # OPTIMIZE: is there a more efficient way to do this?

    return workflow_names


def get_list_of_all_workflows():
    """
    Returns a list of all the workflows of all types.

    This utility was make specifically for the CLI where we print out all
    workflow names for the user.
    """

    workflow_names = []
    for flow_type in ALL_WORKFLOW_TYPES:

        workflow_type_names = get_list_of_workflows_by_type(flow_type)

        # we add the type to the start of each workflow name and switch underscores
        # to dashes bc they are more reader-friendly
        workflow_type_names = [
            flow_type.replace("_", "-") + "/" + w.replace("_", "-")
            for w in workflow_type_names
        ]

        workflow_names += workflow_type_names

    return workflow_names
