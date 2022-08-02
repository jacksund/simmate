# -*- coding: utf-8 -*-

"""
This module hosts common utilities for Simmate's workflow library. This includes
functions for grabbing all available workflows as well as dynamically loading
a workflow using its name.
"""

import os
import yaml
import shutil
import pkgutil
from typing import List
from importlib import import_module

from simmate import workflows
from simmate.utilities import get_directory, make_archive
from simmate.workflow_engine import Workflow


def get_workflow_types():
    """
    Grabs all workflow types, which is also all "Project Names" and all of the
    submodules listed in the `simmate.workflows` module.

    Gives names in the format with all lowercase and hypens, such as "relaxation"
    or "static-energy"
    """

    workflow_types = [
        submodule.name.replace("_", "-")
        for submodule in pkgutil.iter_modules(workflows.__path__)
        if submodule.name != "utilities"
    ]

    workflow_types.sort()

    return workflow_types


def get_list_of_workflows_by_type(
    flow_type: str,
    full_name: bool = True,
) -> List[str]:
    """
    Returns a list of all the workflows located in the given module.
    """

    # Make sure the type is supported
    workflow_types = get_workflow_types()
    if flow_type not in workflow_types:
        raise TypeError(
            f"{flow_type} is not allowed. Please use a workflow type from this"
            f" list: {workflow_types}"
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
        # OPTIMIZE: line below --> issubclass(attr, Workflow) --> raises error
        if hasattr(attr, "run_config") and attr.__name__ != "Workflow":
            # attr is now a workflow object (such as Relaxation__Vasp__Matproj)
            # and we can grab whichever name we'd like from it.
            if full_name:
                workflow_name = attr.name_full
            else:
                workflow_name = attr.name_preset
            # and add the name to our list
            workflow_names.append(workflow_name)
    # OPTIMIZE: is there a more efficient way to do this?

    workflow_names.sort()
    return workflow_names


def get_list_of_all_workflows() -> List[str]:
    """
    Returns a list of all the workflows of all types.

    This utility was make specifically for the CLI where we print out all
    workflow names for the user.
    """

    workflow_names = []
    for flow_type in get_workflow_types():
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

    matproj_workflow = get_workflow("static-energy.vasp.matproj")
    ```

    ...does the same exact thing as...
    ``` python
    from simmate.workflows.static_energy import StaticEnergy__Vasp__Matproj
    ```

    Note the naming of workflows therefore follows the format:
    ``` python

    # an example import of some workflow
    from simmate.workflows.example_module import example_workflow_class

    ```

    #### Parameters

    - `workflow_name`:
        Name of the workflow to load. Examples include "relaxation.vasp.matproj",
        "static-energy.vasp.quality01", and "diffusion.vasp.all-paths"

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

    # parse the workflow name. (e.g. static-energy.vasp.mit --> static_energy + vasp + mit)
    project_name, calculator_name, preset_name = workflow_name.replace("-", "_").split(
        "."
    )

    # Combine the names into the full class name
    # (e.g. static_energy + vasp + mit --> StaticEnergy__Vasp__Mit)
    workflow_class_name = "__".join(
        [
            n.title().replace("_", "")
            for n in [project_name, calculator_name, preset_name]
        ]
    )

    # The naming convention matches the import path
    # BUG: What about user workflows...? Should I try each custom app import?
    workflow_module = import_module(f"simmate.workflows.{project_name}")

    # If requested, print a message indicating the import we are using
    if print_equivalent_import:
        print(
            "Using: \n\n\t"
            f"from simmate.workflows.{project_name} import {workflow_class_name} \n\n"
            "You can find the source code for this workflow in the follwing module: \n\n\t"
            f"simmate.calculators.{calculator_name}.workflows.{project_name}"
        )

    # and import the workflow
    workflow = getattr(workflow_module, workflow_class_name)

    return workflow


def load_results_from_directories(
    base_directory: str = ".",
):
    """
    Goes through a given directory and finds all "simmate-task-" folders and zip
    archives present. The simmate_metadata.yaml file is used in each of these
    to load results into the database. All folders will be converted to archives
    once they've been loaded.

    #### Parameters

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
            results_db = workflow.database_table.from_directory(foldername)

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
        for parameter in workflow.parameter_names:
            if parameter not in unique_parameters and parameter not in [
                "kwargs",
                "cls",
            ]:
                unique_parameters.append(parameter)

    # for consistency, we sort these alphabetically
    unique_parameters.sort()

    return unique_parameters
