# -*- coding: utf-8 -*-

import os
import yaml
import shutil

from importlib import import_module

from simmate.utilities import get_directory, make_archive
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


def get_workflow(
    workflow_name: str,
    precheck_flow_exists: bool = False,
    print_equivalent_import: bool = False,
):
    """
    This is a utility for that grabs a workflow from the simmate workflows.

    This is typically used when we need to dynamically import a workflow, such
    as when calling a workflow through the command-line. We recommend avoiding
    this function when possible, and instead directly import your workflow.

    For example...
    ``` python
    from simmate.workflows.utilities import get_workflow

    matproj_workflow = get_workflow("relaxation/matproj")
    ```

    ...does the same exact thing as...
    ``` python
    from simmate.workflows.relaxation import matproj_workflow
    ```

    Note the naming of workflows therefore follows the format:
    ``` python

    # an example import of some workflow
    from simmate.workflows.example_module import example_flowtype_workflow

    # an example of how what this workflows name would be
    workflow_name = "example-module/example-flowtype"
    ```

    Parameters
    ----------
    - `workflow_name`:
        Name of the workflow to load. Examples include "relaxation/matproj",
        "static-energy/quality01", and "diffusion/all-paths"
    - `precheck_flow_exists`:
        Whether to check if the workflow actually exists before attempting the
        import. Note, this requires loading all other workflows in order to make
        this check, so it slows down the function substansially. Defaults to false.
    - `print_equivalent_import`:
        Whether to print a message indicating the equivalent import for this
        workflow. Typically this is only useful for beginners using the CLI.
        Defaults to false.
    """

    # make sure we have a proper workflow name provided.
    # This is optional because it is slow and loads all other workflows, rather
    # than just the one we are interested in.
    if precheck_flow_exists:
        allowed_workflows = get_list_of_all_workflows()
        if workflow_name not in allowed_workflows:
            raise ModuleNotFoundError(
                "The workflow you provided isn't known. Make sure you don't have any "
                "typos! If you want a list of all available workflows, use the command "
                "`simmate workflows list-all`. You can also interactively explore "
                "workflows with `simmate workflows explore`"
            )

    # parse the workflow name. (e.g. static-energy/mit --> static-energy + mit)
    type_name, preset_name = workflow_name.split("/")
    type_name = type_name.replace("-", "_")
    preset_name = preset_name.replace("-", "_")

    # The naming convention matches the import path, so we can load the workflow
    workflow_module = import_module(f"simmate.workflows.{type_name}")

    # If requested, print a message indicating the import we are using
    if print_equivalent_import:
        print(
            f"Using... from simmate.workflows.{type_name} import {preset_name}_workflow"
        )
    # This line effectly does the same as...
    #   from simmate.workflows.{type_name} import {preset_name}_workflow
    workflow = getattr(workflow_module, f"{preset_name}_workflow")

    return workflow


def load_results_from_directories(
    base_directory: str = ".",
):
    """
    Goes through a given directory and finds all "simmate-task-" folders and zip
    archives present. The simmate_metadata.yaml file is used in each of these
    to load results into the database. All folders will be converted to archives
    once they've been loaded.

    Parameters
    ----------
    - `base_directory`:
        The main directory that will contain folders to archive. Defaults to the
        working directory.
    """
    # load the full path to the desired directory
    directory = get_directory(base_directory)

    # grab all files/folders in this directory and then limit this list to those
    # that are...
    #   1. folders
    #   2. start with "simmate-task-"
    #   3. haven't been modified for at least time_cutoff
    foldernames = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if "simmate-task-" in os.path.basename(f)
    ]

    # Now go through this list and archive the folders that met the criteria
    # and load the data from each.
    for foldername in foldernames:

        # Print message for monitoring progress.
        # TODO: consider switching to tqdm
        print(f"Loading data from... \n\t{foldername}")

        # If we have a zip file, we need to unpack it before we can read results
        if not os.path.isdir(foldername):
            shutil.unpack_archive(
                filename=foldername,
                extract_dir=directory,
            )
            # remove the ".zip" ending for our folder
            foldername = foldername.removesuffix(".zip")

        # Grab the metadata file which tells us key information
        filename = os.path.join(foldername, "simmate_metadata.yaml")
        with open(filename) as file:
            metadata = yaml.full_load(file)

        # see which workflow was used -- which also tells us the database table
        workflow_name = metadata["workflow_name"]
        workflow = get_workflow(workflow_name)

        # now load the data
        results_db = workflow.result_table.from_directory(foldername)

        # use the metadata to update the other fields
        results_db.source = metadata["source"]
        results_db.prefect_flow_run_id = metadata["prefect_flow_run_id"]

        # note the directory might have been moved from when this was originally
        # ran vs where it is now. Therefore, we update the folder location here.
        results_db.directory = foldername

        # Now save the results and convert the folder to an archive
        results_db.save()
        make_archive(foldername)
