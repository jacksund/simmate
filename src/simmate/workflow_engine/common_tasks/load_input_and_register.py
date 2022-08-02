# -*- coding: utf-8 -*-

import os
import yaml
from typing import Any

from prefect import task
from prefect.context import FlowRunContext

from simmate.utilities import get_directory, copy_directory
from simmate.workflow_engine import Workflow

# OPTIMIZE: consider splitting this task into load_structure, load_directory,
# and register_calc so that our flow_visualize looks cleaner

# OPTIMIZE: Customized workflows cause a lot of special handling in this task
# so it may be worth isolating these into a separate task.


@task
def load_input_and_register(
    register_run: bool = True,
    **parameters: Any,
) -> dict:
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

    `register_run` allows us to skip the database step if the database_table
    isn't properly set yet. This input is a temporary fix for the
    diffusion/from-images workflow.

    `copy_previous_directory` is only used when we are pulling a structure from a
    previous calculation. If copy_previous_directory=True, then the directory
    parameter is ignored.

    `**parameters` includes all parameters and anything extra that you want saved
    to simmate_metadata.yaml
    """

    # ---------------------------------------------------------------------

    # Grab the workflow object as we need to reference some of its attributes.
    # In addition, we will also use the flow run id for registration.
    run_context = FlowRunContext.get()
    workflow_name = run_context.flow.name
    prefect_flow_run_id = str(run_context.flow_run.id)
    workflow = run_context.flow.simmate_workflow

    # ---------------------------------------------------------------------

    # STEP 1: clean parameters

    parameters_cleaned = Workflow._deserialize_parameters(**parameters)

    # ---------------------------------------------------------------------

    # STEP 1b: Determine the "primary" input to use for setting the
    # source (and previous directory)
    # OPTIMIZE: Is there a better way to do this?

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
        previous_directory = primary_input_cleaned.database_object.directory

        # Copy over all files except simmate one (we have no need for the
        # summaries or error archives)
        copy_directory(
            directory_old=previous_directory,
            directory_new=directory_cleaned,
            ignore_simmate_files=True,
        )

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
        # assert
        if not source == primary_input:
            # only warning for now because this is experimental
            print(
                "\nWARNING: Your source does not match the source of your "
                "primary input. Sources are an experimental feature, so "
                "this will not affect your results. Still, please report "
                "this to our team to help with development. \n\n"
                f"SOURCE: {source} \n\n"
                f"PRIMARY_INPUT: {primary_input} \n\n"
            )
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

    # SPECIAL CASE for customized flows
    if "workflow_base" not in parameters_cleaned:
        parameters_cleaned["source"] = source_cleaned
    else:
        parameters_cleaned["input_parameters"]["source"] = source_cleaned

    # ---------------------------------------------------------------------

    # STEP 4: Register the calculation so the user can follow along in the UI
    # and also see which structures/runs have been submitted aready.

    if register_run:
        Workflow._register_calculation(**parameters_cleaned)

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
        workflow_name=workflow_name,
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
