# -*- coding: utf-8 -*-

import os
import yaml
import shutil

from importlib import import_module

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import MigrationHop

from simmate.utilities import get_directory, make_archive
from simmate.workflow_engine import Workflow, S3Task

from typing import List

WORKFLOW_TYPES = [
    "static-energy",
    "relaxation",
    "population-analysis",
    "band-structure",
    "density-of-states",
    "dynamics",
    "diffusion",
]


def get_list_of_workflows_by_type(
    flow_type: str,
    full_name: bool = True,
) -> List[str]:
    """
    Returns a list of all the workflows located in the given module.
    """

    # Make sure the type is supported
    if flow_type not in WORKFLOW_TYPES:
        raise TypeError(
            f"{flow_type} is not allowed. Please use a workflow type from this"
            f" list: {WORKFLOW_TYPES}"
        )

    # switch the naming convention from "flow-name" to "flow_name".
    flow_type_u = flow_type.replace("-", "_")

    # grab the relevent module
    flow_module = import_module(f"simmate.workflows.{flow_type_u}")

    # This loop goes through all attributes (as strings) of the workflow module
    # and select only those that are workflow or s3tasks.
    workflow_names = []
    for attr_name in dir(flow_module):
        attr = getattr(flow_module, attr_name)
        if isinstance(attr, Workflow) or isinstance(attr, S3Task):
            # We remove the _workflow ending for each because it's repetitve.
            # We also change the name from "flow_name" to "flow-name".
            workflow_name = attr_name.removesuffix("_workflow").replace("_", "-")
            # If requested, convert this to the full name.
            if full_name:
                workflow_name = flow_type + "/" + workflow_name
            workflow_names.append(workflow_name)
    # OPTIMIZE: is there a more efficient way to do this?

    return workflow_names


def get_list_of_all_workflows() -> List[str]:
    """
    Returns a list of all the workflows of all types.

    This utility was make specifically for the CLI where we print out all
    workflow names for the user.
    """

    workflow_names = []
    for flow_type in WORKFLOW_TYPES:
        workflow_names += get_list_of_workflows_by_type(flow_type)

    return workflow_names


def get_workflow(
    workflow_name: str,
    precheck_flow_exists: bool = False,
    print_equivalent_import: bool = False,
) -> Workflow:
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

        # There may be many folders that contain failed or incomplete data.
        # We don't want those to prevent others from being loaded so we put
        # everything in a try/except.
        try:

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

            print("\tSuccessful.")

        except:

            print("\tFailed.")


def get_unique_parameters() -> List[str]:
    """
    Returns a list of all unique parameter names accross all workflows.

    This utility is really just to help developers ensure they are covering
    all cases when implementing new features, so this function isn't actually
    called elsewhere.
    """

    flownames = get_list_of_all_workflows()
    unique_parameters = []
    for flowname in flownames:
        workflow = get_workflow(flowname)
        for parameter in workflow.parameters():
            if parameter.name not in unique_parameters:
                unique_parameters.append(parameter.name)

    return unique_parameters


# TODO: what if I called this within the workflow.run method instead?
# I could have a `_parse_parameters` method for each Workflow class that does this
# right before calling super().run() too
def parse_parameters(**kwargs) -> dict:
    """
    This utility is meant to take a dictionary of parameters for a workflow and
    then convert them to proper python objects.

    For example, a common input parameter for workflows is "structure", which
    can be provided a number of ways:
        - a filename
        - a json string
        - a dictionary pointing to a database entry
        - a toolkit Structure object
        - etc...

    Even though all of these inputs are accepts, `workflow.run` always expects
    a
    """

    # we don't want to pass arguments like command=None or structure=None if the
    # user didn't provide this input parameter. Instead, we want the workflow to
    # use its own default value. To do this, we first check if the parameter
    # is set in our kwargs dictionary and making sure the value is NOT None.
    # If it is None, then we remove it from our final list of kwargs. This
    # is only done for command, directory, and structure inputs -- as these
    # are the three that are typically assumed to be present (see the CLI).

    if not kwargs.get("command", None):
        kwargs.pop("command", None)

    if not kwargs.get("directory", None):
        kwargs.pop("directory", None)

    structure = kwargs.get("structure", None)
    if structure:
        kwargs["structure"] = Structure.from_dynamic(structure)
    else:
        kwargs.pop("structure", None)

    if "structures" in kwargs.keys():
        structure_filenames = kwargs["structures"].split(";")
        kwargs["structures"] = [
            Structure.from_dynamic(file) for file in structure_filenames
        ]

    if "migration_hop" in kwargs.keys():
        migration_hop = MigrationHop.from_dynamic(kwargs["migration_hop"])
        kwargs["migration_hop"] = migration_hop

    if "supercell_start" in kwargs.keys():
        kwargs["supercell_start"] = Structure.from_dynamic(kwargs["supercell_start"])

    if "supercell_end" in kwargs.keys():
        kwargs["supercell_end"] = Structure.from_dynamic(kwargs["supercell_end"])

    return kwargs
