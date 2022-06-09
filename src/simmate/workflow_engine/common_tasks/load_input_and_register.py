# -*- coding: utf-8 -*-

import os
import shutil
import yaml
from typing import Any

import prefect
from prefect import task

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import MigrationHop, MigrationImages
from simmate.utilities import get_directory
from simmate.workflow_engine import Workflow

# OPTIMIZE: consider splitting this task into load_structure, load_directory,
# and register_calc so that our flow_visualize looks cleaner

# OPTIMIZE: Customized workflows cause a lot of special handling in this task
# so it may be worth isolating these into a separate task.


@task
def load_input_and_register(register_run=True, **parameters: Any) -> dict:
    """
    How the input was submitted as a parameter depends on if we are submitting
    to Prefect Cloud, running the flow locally, or even continuing from a
    previous calculation.  Here, we use a task to convert the input to a toolkit
    object and (if requested) provide the directory as well.

    For example, a common input parameter for workflows is "structure", which
    can be provided a number of ways:
        - a filename
        - a json string
        - a dictionary pointing to a database entry
        - a toolkit Structure object
        - etc...
    Even though all of these inputs are accepted, `workflow.run` always expects
    python objects, so this utility converts the input to a toolkit Structure
    object.

    `register_run` allows us to skip the database step if the calculation_table
    isn't properly set yet. This input is a temporary fix for the
    diffusion/from-images workflow.

    `copy_previous_directory` is only used when we are pulling a structure from a
    previous calculation. If copy_previous_directory=True, then the directory
    parameter is ignored.

    `**parameters` includes all parameters and anything extra that you want saved
    to simmate_metadata.yaml
    """
    print(parameters)

    # !!! This function needs a refactor that is waiting on prefect 2.0.
    # In the future, this will be broken into smaller methods and utilities.
    # Prefect 2.0 will allow us to do more pythonic things such as...
    # @flow
    # def example_workflow(**kwargs):
    #     # NOT a prefect task but a normal function
    #     kwargs_cleaned = serialize_parameters(**kwargs)
    #
    #     # a prefect task
    #     result = some_prefect_task(**kwargs_cleaned)

    # ---------------------------------------------------------------------

    # Grab the workflow object as we need to reference some of its attributes.
    # In addition, we will also use the flow run id for registration.

    # BUG: for some reason, this script fails when get_workflow is imported
    # at the top of this file rather than here.
    from simmate.workflows.utilities import get_workflow

    workflow_name = prefect.context.get("flow_name") or parameters.get("workflow_name")
    if not workflow_name:
        raise Exception("Unknown workflow")

    # BUG: I have to do this in order to allow workflows that are from the
    # simmate.workflows module. There should be a better way to handle user
    # created workflows.
    try:
        workflow = get_workflow(workflow_name)
    except:
        workflow = None

    prefect_flow_run_id = prefect.context.flow_run_id

    # ---------------------------------------------------------------------

    # STEP 1: clean parameters

    # we don't want to pass arguments like command=None or structure=None if the
    # user didn't provide this input parameter. Instead, we want the workflow to
    # use its own default value. To do this, we first check if the parameter
    # is set in our kwargs dictionary and making sure the value is NOT None.
    # If it is None, then we remove it from our final list of kwargs. This
    # is only done for command, directory, and structure inputs -- as these
    # are the three that are typically assumed to be present (see the CLI).

    parameters_cleaned = deserialize_parameters(parameters)

    #######
    # SPECIAL CASE: customized workflows have their parameters stored under
    # "input_parameters" instead of the base dict
    if "workflow_base" in parameters.keys():
        # This is a non-modular import that can cause issues and slower
        # run times. We therefore import lazily.
        from simmate.workflows.utilities import get_workflow

        parameters_cleaned["workflow_base"] = get_workflow(parameters["workflow_base"])
        parameters_cleaned["input_parameters"] = deserialize_parameters(
            parameters["input_parameters"]
        )
    #######

    # ---------------------------------------------------------------------

    # STEP 1b: Determine the "primary" input to use for determining the
    # source (and previous directory)
    # !!! Is there a better way to do this?

    # Currently I just set a priority of possible parameters that can be
    # the primary input. I go through each one at a time until I find one
    # that was provided -- then I exit with that parameter's value.
    primary_input = None
    for primary_input_key in ["structure", "migration_hop", "supercell_start"]:
        primary_input = parameters.get(primary_input_key, None)
        primary_input_cleaned = parameters_cleaned.get(primary_input_key, None)
        if primary_input:
            break

    # ---------------------------------------------------------------------

    # STEP 2: Load the directory (and copy over from an old directory if necessary)

    # Start by creating a new directory or grabbing the one given. We create
    # this directory immediately (rather than just passing the name to the
    # S3Task). We do this because NestedWorkflows often use a parent directory
    # to organize results.
    directory = parameters.get("directory", None)
    directory_cleaned = get_directory(directory)

    # if the user requested, we grab the previous directory as well
    copy_previous_directory = parameters.get("copy_previous_directory", None)
    if copy_previous_directory:

        if not primary_input:
            raise Exception(
                "No primary input detected, which is required for copying "
                "past directories. This is an experimental feature so "
                "please contact our team for more help."
            )

        # catch incorrect use of this function
        if not primary_input_cleaned.is_from_past_calc:
            raise Exception(
                "There isn't a previous directory available! Your source "
                "structure must point to a past calculation to use this feature."
            )

        # the past directory should be stored on the input object
        previous_directory = primary_input_cleaned.calculation.directory

        # First check if the previous directory exists. There are several
        # possibilities that we need to check for:
        #   1. directory exists on the same file system and can be found
        #   2. directory exists on the same file system but is now an archive
        #   3. directory/archive is on another file system (requires ssh to access)
        #   4. directory was deleted and unavailable
        # When copying over the directory, we ignore any `simmate_` files
        # that correspond to metadata/results/corrections/etc.
        if os.path.exists(previous_directory):
            # copy the old directory to the new one
            shutil.copytree(
                src=previous_directory,
                dst=directory_cleaned,
                ignore=shutil.ignore_patterns("simmate_*"),
                dirs_exist_ok=True,
            )
        elif os.path.exists(f"{previous_directory}.zip"):
            # unpack the old archive
            shutil.unpack_archive(
                filename=f"{previous_directory}.zip",
                extract_dir=os.path.dirname(previous_directory),
            )
            # copy the old directory to the new one
            shutil.copytree(
                src=previous_directory,
                dst=directory_cleaned,
                ignore=shutil.ignore_patterns("simmate_*"),
                dirs_exist_ok=True,
            )
            # Then remove the unpacked archive now that we copied it.
            # This leaves the original archive behind and unaltered too.
            shutil.rmtree(previous_directory)
        else:
            raise Exception(
                "Unable to locate the previous calculation to copy. Make sure the "
                "past directory is located on the same file system. Directory that "
                f"couldn't be found was... {previous_directory}"
            )
        # TODO: for possibility 3, I could implement automatic copying with
        # the "fabric" python package (uses ssh). I'd also need to store
        # filesystem names (e.g. "WarWulf") to know where to connect.

    # SPECIAL CASE for customized flows
    if "workflow_base" not in parameters_cleaned:
        parameters_cleaned["directory"] = directory_cleaned
    else:
        parameters_cleaned["input_parameters"]["directory"] = directory_cleaned

    # ---------------------------------------------------------------------

    # STEP 3: Load the source of the input object

    source = parameters.get("source", None)

    # If we were given a input from a previous calculation, the source should
    # point directory to that same input. Otherwise we are incorrectly trying
    # to change what the source is.
    # "primary_input and" is added to the start to ensure cleaned input exists
    # and therefore prevent an error/bug.
    if source and primary_input and primary_input_cleaned.is_from_past_calc:
        # note primary_input here is a dictionary
        print(source)
        print(primary_input)
        assert source == primary_input
        source_cleaned = source
    # Check if we have a primary input loaded from a past calculation and
    # default to that as the source.
    elif primary_input and primary_input_cleaned.is_from_past_calc:
        source_cleaned = primary_input
    # Otherwise just use the source given
    elif source:
        source_cleaned = source
    else:
        source_cleaned = None

    parameters_cleaned["source"] = source_cleaned

    # ---------------------------------------------------------------------

    # STEP 4: Register the calculation so the user can follow along in the UI.

    # This is only done if a table is provided. Some special-case workflows
    # don't store calculation information bc the flow is just a quick python
    # analysis.

    if register_run and workflow and workflow.calculation_table:

        # grab the registration kwargs from the parameters provided
        register_kwargs = {
            key: parameters_cleaned.get(key, None) for key in workflow.register_kwargs
        }

        # SPECIAL CASE: for customized workflows we need to convert the inputs
        # back to json for saving to the database. I just use original inputs
        # for now.
        register_kwargs = (
            register_kwargs if "workflow_base" not in parameters_cleaned else parameters
        )

        # load/create the calculation for this workflow run
        calculation = workflow.calculation_table.from_prefect_id(
            id=prefect_flow_run_id,
            **register_kwargs
            if "workflow_base" not in parameters_cleaned
            else parameters,
        )

    # ---------------------------------------------------------------------

    # STEP 5: Write metadata file for user reference

    # convert back to json format. We convert back rather than use the original
    # to ensure the input data is all present. For example, we want to store
    # structure data instead of a filename in the metadata.
    # SPECIAL CASE: "if ..." used to catch customized workflows
    parameters_serialized = (
        Workflow._serialize_parameters(**parameters_cleaned)
        if "workflow_base" not in parameters_cleaned
        else parameters
    )

    # We want to write a file summarizing the inputs used for this
    # workflow run. This allows future users to reproduce the results if
    # desired -- and it also allows us to load old results into a database.
    input_summary = dict(
        workflow_name=workflow.name if workflow else "non-module-flow",
        # this ID is ingored as an input but needed for loading past data
        prefect_flow_run_id=prefect_flow_run_id,
        **parameters_serialized,
    )

    # now write the summary to file in the same directory as the calc.
    input_summary_filename = os.path.join(directory_cleaned, "simmate_metadata.yaml")
    with open(input_summary_filename, "w") as file:
        content = yaml.dump(input_summary)
        file.write(content)

    # ---------------------------------------------------------------------

    # Finally we just want to return the dictionary of cleaned parameters
    # to be used by the workflow
    return parameters_cleaned


def deserialize_parameters(parameters: dict) -> dict:

    parameters_cleaned = parameters.copy()

    if not parameters.get("command", None):
        parameters_cleaned.pop("command", None)

    if not parameters.get("directory", None):
        parameters_cleaned.pop("directory", None)

    structure = parameters.get("structure", None)
    if structure:
        parameters_cleaned["structure"] = Structure.from_dynamic(structure)
    else:
        parameters_cleaned.pop("structure", None)

    if "structures" in parameters.keys():
        structure_filenames = parameters["structures"].split(";")
        parameters_cleaned["structures"] = [
            Structure.from_dynamic(file) for file in structure_filenames
        ]

    if "migration_hop" in parameters.keys():
        migration_hop = MigrationHop.from_dynamic(parameters["migration_hop"])
        parameters_cleaned["migration_hop"] = migration_hop

    if "migration_images" in parameters.keys():
        migration_images = MigrationImages.from_dynamic(parameters["migration_images"])
        parameters_cleaned["migration_images"] = migration_images

    if "supercell_start" in parameters.keys():
        parameters_cleaned["supercell_start"] = Structure.from_dynamic(
            parameters["supercell_start"]
        )

    if "supercell_end" in parameters.keys():
        parameters_cleaned["supercell_end"] = Structure.from_dynamic(
            parameters["supercell_end"]
        )

    return parameters_cleaned
