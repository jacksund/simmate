# -*- coding: utf-8 -*-

"""
This module hosts common utilities for Simmate's workflow library. This includes
functions for grabbing all available workflows as well as dynamically loading
a workflow using its name.
"""

import importlib
import logging
import pkgutil
import shutil
import sys
from pathlib import Path

import yaml
from rich import print

from simmate import workflows
from simmate.configuration.django.settings import extra_apps
from simmate.utilities import get_directory, make_archive
from simmate.workflow_engine import Workflow


def get_all_workflow_names() -> list[str]:
    """
    Returns a list of all the workflows of all types.

    This utility was make specifically for the CLI where we print out all
    workflow names for the user.
    """

    workflow_names = []
    for flow_type in get_all_workflow_types():
        workflow_names += get_workflow_names_by_type(flow_type)

    return workflow_names


def get_all_workflow_types():
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

    # add custom apps
    for flow in get_workflows_from_apps():
        if flow.name_type not in workflow_types:
            workflow_types.append(flow.name_type)

    workflow_types.sort()

    return workflow_types


def get_calculators_by_type(flow_type: str) -> list[str]:
    """
    Returns a list of all the available calculators for a given workflow type.
    """
    # !!! This is largely a copy/paste of code from get_workflow_names_by_type.
    # Consider merging during refactor.

    # Make sure the type is supported
    workflow_types = get_all_workflow_types()
    if flow_type not in workflow_types:
        raise TypeError(
            f"{flow_type} is not allowed. Please use a workflow type from this"
            f" list: {workflow_types}"
        )

    # switch the naming convention from "flow-name" to "flow_name".
    flow_type_u = flow_type.replace("-", "_")

    # grab the relevent module. If this fails, then the user is giving a custom
    # type that isn't in simmate.
    try:
        flow_module = importlib.import_module(f"simmate.workflows.{flow_type_u}")
        is_custom_type = False
    except ModuleNotFoundError:
        is_custom_type = True

    calculator_names = []

    # This loop goes through all attributes (as strings) of the workflow module
    # and select only those that are workflow or s3tasks.
    if not is_custom_type:
        for attr_name in dir(flow_module):
            attr = getattr(flow_module, attr_name)
            # OPTIMIZE: line below --> issubclass(attr, Workflow) --> raises error
            if hasattr(attr, "run_config") and attr.__name__ != "Workflow":
                # attr is now a workflow object (such as Relaxation__Vasp__Matproj)
                # and we can grab whichever name we'd like from it and
                # add the name to our list
                if attr.name_calculator not in calculator_names:
                    calculator_names.append(attr.name_calculator)
        # OPTIMIZE: is there a more efficient way to do this?

    # add custom app calculators
    for flow in get_workflows_from_apps():
        if flow.name_type == flow_type and flow.name_calculator not in calculator_names:
            calculator_names.append(flow.name_calculator)

    calculator_names.sort()
    return calculator_names


def get_workflow_names_by_type(
    flow_type: str,
    calculator_name: str = None,
    full_name: bool = True,
) -> list[str]:
    """
    Returns a list of all the workflows located in the given module.
    """

    # Make sure the type is supported
    workflow_types = get_all_workflow_types()
    if flow_type not in workflow_types:
        raise TypeError(
            f"{flow_type} is not allowed. Please use a workflow type from this"
            f" list: {workflow_types}"
        )

    # switch the naming convention from "flow-name" to "flow_name".
    flow_type_u = flow_type.replace("-", "_")

    # grab the relevent module. If this fails, then the user is giving a custom
    # type that isn't in simmate.
    try:
        flow_module = importlib.import_module(f"simmate.workflows.{flow_type_u}")
        is_custom_type = False
    except ModuleNotFoundError:
        is_custom_type = True

    workflow_names = []

    # This loop goes through all attributes (as strings) of the workflow module
    # and select only those that are workflow or s3tasks.
    if not is_custom_type:
        for attr_name in dir(flow_module):
            attr = getattr(flow_module, attr_name)
            # OPTIMIZE: line below --> issubclass(attr, Workflow) --> raises error
            if hasattr(attr, "run_config") and attr.__name__ != "Workflow":
                # attr is now a workflow object (such as Relaxation__Vasp__Matproj)
                # and we can grab whichever name we'd like from it.

                # if a calculator_name was given, then we need to limit the results
                # to that specific calculator.
                if calculator_name and attr.name_calculator != calculator_name:
                    continue  # Skip those that don't match

                if full_name:
                    workflow_name = attr.name_full
                else:
                    workflow_name = attr.name_preset

                # and add the name to our list
                workflow_names.append(workflow_name)
        # OPTIMIZE: is there a more efficient way to do this?

    # add custom app calculators
    for flow in get_workflows_from_apps():
        if flow.name_type != flow_type:
            continue
        # this follows the same logic as the for-loop above
        if calculator_name and flow.name_calculator != calculator_name:
            continue
        if full_name:
            workflow_name = flow.name_full
        else:
            workflow_name = flow.name_preset
        workflow_names.append(workflow_name)

    workflow_names.sort()
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

    # check if we have a custom workflow first
    if workflow_name in get_workflow_names_from_apps():
        workflow_dict = get_workflows_from_apps(as_dict=True)
        return workflow_dict[workflow_name]

    # First check if the user is providing a custom workflow, where the path is
    # given as "path/to/my/script:my_workflow_obj". If so, we need to load that
    # file and grab the workflow like it's an object from a python module.
    if ":" in workflow_name:

        # Note, windows paths have multiple ":" so we need to use rsplit.
        script_name, workflow_obj_name = workflow_name.rsplit(":", 1)
        script_name = Path(script_name)
        module_name = script_name.stem

        # No idea how this works, but its from the official docs... This just
        # loads our python file as if was a module
        # https://stackoverflow.com/questions/19009932/
        # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
        spec = importlib.util.spec_from_file_location(module_name, script_name)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # now grab the workflow from the module!
        workflow = getattr(module, workflow_obj_name)

        return workflow

    # make sure we have a proper workflow name provided.
    # This is optional because it is slow and loads all other workflows, rather
    # than just the one we are interested in.
    if precheck_flow_exists:
        allowed_workflows = get_all_workflow_names()
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
    workflow_module = importlib.import_module(f"simmate.workflows.{project_name}")

    # If requested, print a message indicating the import we are using
    if print_equivalent_import:
        print("\n\n[bold green]Using:")
        print(
            f"\n\tfrom simmate.workflows.{project_name} import {workflow_class_name} \n\n"
            "You can find the source code for this workflow in the follwing module: \n\n\t"
            f"simmate.calculators.{calculator_name}.workflows.{project_name}"
        )

    # and import the workflow
    workflow = getattr(workflow_module, workflow_class_name)

    return workflow


def load_results_from_directories(base_directory: Path | str = "."):
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
        directory / f for f in directory.iterdir() if "simmate-task-" in f.name
    ]

    # Now go through this list and archive the folders that met the criteria
    # and load the data from each.
    for foldername in foldernames:

        # Print message for monitoring progress.
        logging.info(f"Loading data from {foldername}")

        # There may be many folders that contain failed or incomplete data.
        # We don't want those to prevent others from being loaded so we put
        # everything in a try/except.
        try:

            # If we have a zip file, we need to unpack it before we can read results
            if not foldername.is_dir():
                shutil.unpack_archive(
                    filename=foldername,
                    extract_dir=directory,
                )
                # remove the ".zip" ending for our folder
                foldername = foldername.removesuffix(".zip")

            # Grab the metadata file which tells us key information
            filename = foldername / "simmate_metadata_01.yaml"
            with filename.open() as file:
                metadata = yaml.full_load(file)

            # see which workflow was used -- which also tells us the database table
            workflow_name = metadata["workflow_name"]
            workflow = get_workflow(workflow_name)

            # now load the data
            results_db = workflow.database_table.from_directory(foldername)

            # use the metadata to update the other fields
            results_db.source = metadata["source"]
            results_db.run_id = metadata["run_id"]

            # note the directory might have been moved from when this was originally
            # ran vs where it is now. Therefore, we update the folder location here.
            results_db.directory = foldername

            # Now save the results and convert the folder to an archive
            results_db.save()
            make_archive(foldername)

            logging.info("Successfully loaded into database.")

        except:
            logging.warning("Failed to load into database")


def get_unique_parameters() -> list[str]:
    """
    Returns a list of all unique parameter names accross all workflows.

    This utility is really just to help developers ensure they are covering
    all cases when implementing new features, so this function isn't actually
    called elsewhere.
    """

    flownames = get_all_workflow_names()
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


def get_workflow_names_from_apps(apps_to_search: list[str] = extra_apps) -> list[str]:
    return [flow.name_full for flow in get_workflows_from_apps(apps_to_search)]


def get_workflows_from_apps(
    apps_to_search: list[str] = extra_apps,
    as_dict: bool = False,
):
    app_workflows = []
    for app_name in apps_to_search:
        app_modulename = app_name.split(".")[0]
        try:
            app_module = importlib.import_module(f"{app_modulename}.workflows")
        except:
            logging.warning(
                f"Failed to load workflows from {app_name}. Did you make sure "
                "there is a workflows.py file or module present?"
            )
            continue

        # iterate through each available object in the workflows file and find
        # which ones are workflow objects
        for workflow_name in app_module.__all__:
            workflow = getattr(app_module, workflow_name)
            if workflow not in app_workflows:
                app_workflows.append(workflow)

    return (
        app_workflows
        if not as_dict
        else {flow.name_full: flow for flow in app_workflows}
    )
