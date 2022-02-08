# -*- coding: utf-8 -*-

import click

from typing import List


@click.group()
def workflows():
    """A group of commands for running workflows or viewing their settings."""
    pass


def get_workflow(workflow_name: str):
    """
    This is a utility for click (cli) that grabs a workflow from the simmate
    workflows. If the workflow can't be found, it raises a ClickException.

    Parameters
    ----------
    workflow_name : str
        Name of the workflow to grab (e.g. relaxation-matproj)
    """

    from simmate.workflows.utilities import get_list_of_all_workflows

    allowed_workflows = get_list_of_all_workflows()

    # make sure we have a proper workflow name provided
    if workflow_name not in allowed_workflows:
        raise click.ClickException(
            "The workflow you provided isn't known. Make sure you don't have any "
            "typos! If you want a list of all available workflows, use the command "
            "`simmate workflows list-all`. You can also interactively explore "
            "workflows with `simmate workflows explore`"
        )

    from importlib import import_module

    # parse the workflow name. (e.g. static-energy/mit --> static-energy + mit)
    type_name, preset_name = workflow_name.split("/")
    type_name = type_name.replace("-", "_")
    preset_name = preset_name.replace("-", "_")

    # The naming convention matches the import path, so we can load the workflow
    workflow_module = import_module(f"simmate.workflows.{type_name}")
    print(f"simmate.workflows.{type_name}")
    print(f"{preset_name}_workflow")
    workflow = getattr(workflow_module, f"{preset_name}_workflow")

    return workflow


def list_options(options: List) -> int:
    """
    This is a utility for click (cli) that prints of list of items as a numbered
    list. It prompts users to select an option from the list.

    For example, `["item1", "item2", "item3"]` would print...
    ```
        (01) item1
        (02) item2
        (03) item3
    ```

    Parameters
    ----------
    - `options`:
        a list of strings to choose from

    Returns
    --------
    - `selected_index`:
        The integer value of the choice selected. This will follw python indexing
        so the index of the options list. (e.g. if item1 was selected, 0 would be
        returned)

    """

    for i, item in enumerate(options):
        number = str(i + 1).zfill(2)
        click.echo(f"\t({number}) {item}")

    # Have the user select an option. We use -1 because indexing count is from 0, not 1.
    selected_index = click.prompt("\n\nPlease choose a number:", type=int) - 1

    if selected_index >= len(options) or selected_index < 0:
        raise click.ClickException(
            "Number does not match any the options provided. Exiting."
        )

    click.echo(f"You have selectd `{options[selected_index]}`.")

    return selected_index


@workflows.command()
def explore():
    """
    Let's you interactively view all available workflows and see the documentation
    on the one you select.
    """

    click.echo("\nGathering all available workflows...")
    from simmate.workflows.utilities import (
        ALL_WORKFLOW_TYPES,
        get_list_of_workflows_by_type,
    )

    click.echo("\n\nWhat type of analysis are you interested in?")
    types_cleaned = [t.replace("_", " ") for t in ALL_WORKFLOW_TYPES]
    type_index = list_options(types_cleaned)
    selected_type = ALL_WORKFLOW_TYPES[type_index]

    # TODO: have the user select a calculator for this analysis. For now,
    # we are assuming VASP because those are our only workflows

    click.echo("\n\nWhat settings preset do you want to see the description for?")
    presets = [t for t in get_list_of_workflows_by_type(selected_type)]
    present_index = list_options(presets)
    selected_preset = presets[present_index]

    final_workflow_name = selected_type.replace("_", "-") + "/" + selected_preset
    click.echo(f"\n\n===================== {final_workflow_name} =====================")

    # now we load this workflow and print the docstring.
    workflow = get_workflow(final_workflow_name)

    click.echo(workflow.__doc__)

    click.echo("==================================================================")


@workflows.command()
def list_all():
    """
    This lists off all available workflows.
    """

    click.echo("Gathering all available workflows...")

    from simmate.workflows.utilities import get_list_of_all_workflows

    click.echo("These are the workflows that have been registerd:")
    all_workflows = get_list_of_all_workflows()
    for i, workflow in enumerate(all_workflows):
        # Replace underscores with dashes for consistency with click
        workflow_dash = workflow.replace("_", "-")
        workflow_number = str(i + 1).zfill(2)
        click.echo(f"\t({workflow_number}) {workflow_dash}")  # gives "(1) example-flow"


@workflows.command()
@click.argument("workflow_name")
def show_config(workflow_name):
    """
    If the workflow is a single task, the calculation's configuration settings
    are displayed. For example, a VASP workflow will show a dictionary that
    details how INCAR settings are selected.
    """

    click.echo("LOADING WORKFLOW...")
    workflow = get_workflow(workflow_name)

    click.echo("PRINTING WORKFLOW CONFIG...")

    # Not all workflows have a single config because some are NestWorkflows,
    # meaning they are made of multiple smaller workflows.
    if hasattr(workflow, "s3task"):
        workflow.s3task.print_config()
    elif hasattr(workflow, "s3tasks"):
        raise click.ClickException(
            "This is a NestedWorkflow, meaning it is made up of multiple smaller "
            "workflows. We have not added a show-config feature for these yet. "
            "This will be added before version 0.0.0 though."
        )


@workflows.command()
@click.argument("workflow_name")
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "--directory",
    "-d",
    default=None,
    help="the folder to write input file in. Defaults to <workflow_name>_input",
)
def setup_only(workflow_name, filename, directory):
    """
    If the workflow is a single task, the calculation is set up but not ran. This
    is useful when you just want the input files to view/edit.
    """

    click.echo("LOADING STRUCTURE AND WORKFLOW...")
    from simmate.toolkit import Structure

    workflow = get_workflow(workflow_name)
    structure = Structure.from_file(filename)

    click.echo("WRITING INPUT FILES...")

    # if no folder was given, just name it after the workflow. We also replace
    # spaces with underscores
    from simmate.utilities import get_directory

    if not directory:
        directory = get_directory(f"{workflow.name}_inputs".replace(" ", "_"))

    # Not all workflows have a single input because some are NestWorkflows,
    # meaning they are made of multiple smaller workflows.
    if hasattr(workflow, "s3task"):
        workflow.s3task().setup(structure, directory)
    elif hasattr(workflow, "s3tasks"):
        raise click.ClickException(
            "This is a NestedWorkflow, meaning it is made up of multiple smaller "
            "workflows. We have not added a setup-only feature for these yet."
        )

    click.echo(f"Done! Your input files are located in {directory}")


# These context settings let us pass extra kwargs, as some workflows have unique
# inputs (e.g. structures, migration_hop, etc. instead of a structure input).
# This is also why we have pass_context and then the kwarg context.
@workflows.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.argument("workflow_name")
@click.option(
    "--structure",
    "-s",
    default=None,
    type=click.Path(exists=True),
    help="filename of the structure used for this workflow (note, not all workflows use this arg)",
)
@click.option(
    "--command",
    "-c",
    default=None,
    help="the command used to call call the calculator (e.g. 'mpirun -n 12 vasp_std > vasp.out')",
)
@click.option(
    "--directory",
    "-d",
    default=None,
    help="the folder to run this workflow in. Defaults to simmate-task-12345, where 12345 is randomized",
)
@click.pass_context
def run(context, workflow_name, structure, command, directory):
    """Runs a workflow using an input structure file"""

    click.echo("LOADING WORKFLOW & INPUT PARAMETERS...")
    from simmate.toolkit import Structure

    workflow = get_workflow(workflow_name)

    # ---- Parsing parameters ----

    # we don't want to pass arguments like command=None or structure=None if the
    # user didn't provide this input. Instead, we want the workflow to use
    # its own default value. To do this, we pass the command input as a kwarg
    # or an empty dict if it wasn't given.

    # The extra keywords passed are given as a list such as...
    #   ["--arg1", "val1", "--arg2", "val2",]
    # Using code from stack overflow, we parse that data into a dictionary.
    #   https://stackoverflow.com/questions/32944131/
    # If there's any issue parsing the data, we alert the user with a hint.
    try:
        extra_kwargs = {
            context.args[i][2:]: context.args[i + 1]
            for i in range(0, len(context.args), 2)
        }
    except:
        raise click.ClickException(
            "This workflow command appears to be improperly formatted. \n"
            "When giving workflow parameters, make sure you provide both the \n"
            "keyword and the value (such as `--example_kwarg example_value`)."
        )

    if command:
        extra_kwargs["command"] = command

    # The structure input (which is optional) is given as a filename, which
    # we need to load as toolkit object. This is also the case for a number
    # of inputs like migration_hop, structures, etc.
    if structure:
        extra_kwargs["structure"] = Structure.from_file(structure)

    if "structures" in extra_kwargs.keys():
        structure_filenames = extra_kwargs["structures"].split(";")
        extra_kwargs["structures"] = [
            Structure.from_file(file) for file in structure_filenames
        ]

    if "migration_hop" in extra_kwargs.keys():
        from simmate.toolkit.diffusion import MigrationHop

        migration_hop = MigrationHop.from_dynamic(extra_kwargs["migration_hop"])
        extra_kwargs["migration_hop"] = migration_hop

    if "supercell_start" in extra_kwargs.keys():
        extra_kwargs["supercell_start"] = Structure.from_file(
            extra_kwargs["supercell_start"]
        )

    if "supercell_end" in extra_kwargs.keys():
        extra_kwargs["supercell_end"] = Structure.from_file(
            extra_kwargs["supercell_end"]
        )

    # ---- end of parsing parameters

    click.echo("RUNNING WORKFLOW...")

    result = workflow.run(
        directory=directory,
        **extra_kwargs,
    )

    # Let the user know everything succeeded
    # if result.is_successful():
    #     click.echo("Success! All results are also stored in your database.")
    # BUG: we remove this temporarily because we have s3tasks ran through this
    # module. When we add their database components, this will be removed.


@workflows.command()
@click.argument("workflow_name")
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "--command",
    "-c",
    default=None,
    help="the command used to call call the calculator (e.g. 'mpirun -n 12 vasp_std > vasp.out')",
)
@click.option(
    "--directory",
    "-d",
    default=None,
    help="the folder to run this workflow in. Defaults to simmate-task-12345, where 12345 is randomized",
)
def run_cloud(workflow_name, filename, command, directory):
    """Runs a workflow using an input structure file"""

    click.echo("LOADING STRUCTURE AND WORKFLOW...")
    from simmate.toolkit import Structure

    workflow = get_workflow(workflow_name)
    structure = Structure.from_file(filename)

    click.echo("RUNNING WORKFLOW...")

    # we don't want to pass command=None if the user didn't provide one. Instead
    # we want the workflow to use its own default value. To do this, we pass
    # the command input as a kwarg -- or an empty dict if it wasn't given.
    command_kwargs = {"command": command} if command else {}

    result = workflow.run_cloud(
        structure=structure,
        directory=directory,
        **command_kwargs,
    )

    # Let the user know everything succeeded
    if result.is_successful():
        click.echo("Success! All results are also stored in your database.")
