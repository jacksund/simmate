# -*- coding: utf-8 -*-

from typing import List

import click
from click import Context


@click.group()
def workflows():
    """A group of commands for running workflows or viewing their settings."""
    pass


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

    #### Parameters

    - `options`:
        a list of strings to choose from

    #### Returns

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


def parse_parameters(context: Context) -> dict:
    """
    This is a utility for click (cli) that formats input parameters for workflow
    runs. It accounts for recieving a `click.Context` object and ensures we
    return a dictionary.

    In order to provide a context, make sure the click command has the following:

    ``` python
    @click.command(
        context_settings=dict(
            ignore_unknown_options=True,
            allow_extra_args=True,
        )
    )
    @click.pass_context
    def example(context):
        pass
    ```

    These context settings let us pass extra kwargs, as some workflows have unique
    inputs (e.g. structures, migration_hop, etc. instead of a structure input).
    This is also why we have pass_context and then the kwarg context.
    """

    # The extra keywords passed are given as a list such as...
    #   ["--arg1", "val1", "--arg2", "val2",]
    # Using code from stack overflow, we parse that data into a dictionary.
    #   https://stackoverflow.com/questions/32944131/
    # If there's any issue parsing the data, we alert the user with a hint.
    try:
        kwargs_cleaned = {
            context.args[i][2:]: context.args[i + 1]
            for i in range(0, len(context.args), 2)
        }

    except:
        raise click.ClickException(
            "This workflow command appears to be improperly formatted. \n"
            "When giving workflow parameters, make sure you provide both the \n"
            "keyword and the value (such as `--example_kwarg example_value`)."
        )

    return kwargs_cleaned


@workflows.command()
def explore():
    """
    Let's you interactively view all available workflows and see the documentation
    on the one you select.
    """

    click.echo("\nGathering all available workflows...")
    from simmate.workflows.utilities import (
        get_workflow_types,
        get_list_of_workflows_by_type,
        get_workflow,
    )

    click.echo("\n\nWhat type of analysis are you interested in?")
    workflow_types = get_workflow_types()
    type_index = list_options(workflow_types)
    selected_type = workflow_types[type_index]

    # TODO: have the user select a calculator for this analysis. For now,
    # we are assuming VASP because those are our only workflows

    click.echo("\n\nWhat settings preset do you want to see the description for?")
    presets = get_list_of_workflows_by_type(selected_type, full_name=False)
    present_index = list_options(presets)
    selected_preset = presets[present_index]

    final_workflow_name = selected_type + ".vasp." + selected_preset
    # BUG: I assume vasp for now, but this should change when I add workflows
    # from new calculators.

    click.echo(f"\n\n===================== {final_workflow_name} =====================")

    # now we load this workflow and print the docstring.
    workflow = get_workflow(
        workflow_name=final_workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )

    click.echo("Description:")
    click.echo(workflow.__doc__)

    click.echo("Parameters:")
    workflow.show_parameters()

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
        workflow_number = str(i + 1).zfill(2)
        click.echo(f"\t({workflow_number}) {workflow}")  # gives "(01) example-flow"


@workflows.command()
@click.argument("workflow_name")
def show_config(workflow_name):
    """
    If the workflow is a single task, the calculation's configuration settings
    are displayed. For example, a VASP workflow will show a dictionary that
    details how INCAR settings are selected.
    """

    click.echo("LOADING WORKFLOW...")
    from simmate.workflows.utilities import get_workflow

    workflow = get_workflow(
        workflow_name=workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )

    click.echo("PRINTING WORKFLOW CONFIG...")

    # Not all workflows have a single config because some are NestWorkflows,
    # meaning they are made of multiple smaller workflows.
    if workflow.s3task:
        workflow.s3task.print_config()
    else:
        raise click.ClickException(
            "This is not a S3Task-based workflow. It is likely a NestedWorkflow, "
            "meaning it is made up of multiple smaller workflows. We have not "
            "added a show-config feature for these yet. "
        )


@workflows.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.argument("workflow_name")
@click.pass_context
def setup_only(context, workflow_name):
    """
    If the workflow is a single task, the calculation is set up but not ran. This
    is useful when you just want the input files to view/edit.
    """

    click.echo("LOADING STRUCTURE AND WORKFLOW...")
    from simmate.toolkit import Structure
    from simmate.workflows.utilities import get_workflow

    workflow = get_workflow(
        workflow_name=workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )
    kwargs_input = parse_parameters(context=context)
    kwargs_cleaned = workflow._deserialize_parameters(**kwargs_input)

    click.echo("WRITING INPUT FILES...")

    # if no folder was given, just name it after the workflow. We also replace
    # spaces with underscores
    from simmate.utilities import get_directory

    directory = kwargs_cleaned.get("directory", None)
    if not directory:
        directory = get_directory(f"{workflow.name_full}.SETUP-ONLY")
        kwargs_cleaned["directory"] = directory

    # Not all workflows have a single input because some are NestWorkflows,
    # meaning they are made of multiple smaller workflows.
    if workflow.s3task:
        workflow.s3task.setup(**kwargs_cleaned)
    else:
        raise click.ClickException(
            "This is not a S3Task-based workflow. It is likely a NestedWorkflow, "
            "meaning it is made up of multiple smaller workflows. We have not "
            "added a setup-only feature for these yet. "
        )

    click.echo(f"Done! Your input files are located in {directory}")


@workflows.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.argument("workflow_name")
@click.pass_context
def run(context, workflow_name):
    """Runs a workflow using provided parameters"""

    click.echo("LOADING WORKFLOW & INPUT PARAMETERS...")

    from simmate.workflows.utilities import get_workflow

    workflow = get_workflow(
        workflow_name=workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )
    kwargs_cleaned = parse_parameters(context=context)

    click.echo("RUNNING WORKFLOW...")

    result = workflow.run(**kwargs_cleaned)

    # Let the user know everything succeeded
    if result.is_completed():
        click.echo("Success! All results are also stored in your database.")


@workflows.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.argument("workflow_name")
@click.pass_context
def run_cloud(context, workflow_name):
    """Submits a workflow to Prefect cloud"""

    click.echo("LOADING WORKFLOW & INPUT PARAMETERS...")

    from simmate.workflows.utilities import get_workflow

    workflow = get_workflow(
        workflow_name=workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )
    kwargs_cleaned = parse_parameters(context=context)

    click.echo("RUNNING WORKFLOW...")

    result = workflow.run_cloud(**kwargs_cleaned)

    # Let the user know everything succeeded
    if result.is_completed():
        click.echo("Success! All results are also stored in your database.")


@workflows.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.argument("filename", type=click.Path(exists=True))
def run_yaml(filename):
    """Runs a workflow where parameters are loaded from a yaml file."""

    click.echo("LOADING WORKFLOW & INPUT PARAMETERS...")

    import yaml

    with open(filename) as file:
        parameters = yaml.full_load(file)  # this is updated below

    from simmate.workflows.utilities import get_workflow

    workflow = get_workflow(
        # we pop the workflow name so that it is also removed from the rest of kwargs
        workflow_name=parameters.pop("workflow_name"),
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )

    # -------------------------------------------------------------------------

    # SPECIAL CASE -- Running customized workflows from yaml.
    # !!! When prefect 2.0 is available, I will be able to use **kwargs as an
    # input for workflow parameters -- in which case, I can move this functionality
    # to load_input_and_register.

    # For customized workflows, we need to completely change the format
    # that we provide the parameters. Customized workflows expect parameters
    # broken into a dictionary of
    #   {"workflow_base": ..., "input_parameters":..., "updated_settings": ...}
    if "workflow_base" in parameters.keys():

        parameters["input_parameters"] = {}
        parameters["updated_settings"] = {}

        for key, update_values in list(parameters.items()):
            # Skip the base keys
            if key in [
                "workflow_base",
                "input_parameters",
                "updated_settings",
            ]:
                continue
            # if there is no prefix, then we have a normal input parameter
            elif not key.startswith("custom__"):
                parameters["input_parameters"][key] = parameters.pop(key)
            # Otherwise remove the prefix and add it to the custom settings.
            else:
                key_cleaned = key.removeprefix("custom__")
                parameters["updated_settings"][key_cleaned] = parameters.pop(key)

    # -------------------------------------------------------------------------

    click.echo("RUNNING WORKFLOW...")

    result = workflow.run(**parameters)

    # Let the user know everything succeeded
    if result.is_completed():
        click.echo("Success! All results are also stored in your database.")


# explicitly list functions so that pdoc doesn't skip them
__all__ = [
    "workflows",
    "explore",
    "list_all",
    "show_config",
    "setup_only",
    "run",
    "run_cloud",
    "run_yaml",
    "list_options",
    "parse_parameters",
]
