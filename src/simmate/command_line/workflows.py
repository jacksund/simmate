# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import typer
from rich import print
from typer import Context

workflows_app = typer.Typer(rich_markup_mode="markdown")


@workflows_app.callback(no_args_is_help=True)
def workflows():
    """A group of commands for running workflows or viewing their settings"""
    pass


def list_options(options: list) -> int:
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
        print(f"\t({number}) {item}")

    # Have the user select an option. We use -1 because indexing count is from 0, not 1.
    selected_index = typer.prompt("\n\nPlease choose a number:", type=int) - 1

    if selected_index >= len(options) or selected_index < 0:
        raise typer.BadParameter(
            "Number does not match any the options provided. Exiting."
        )

    print(f"You have selectd `{options[selected_index]}`.")

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
        raise typer.BadParameter(
            "This workflow command appears to be improperly formatted. \n"
            "When giving workflow parameters, make sure you provide both the \n"
            "keyword and the value (such as `--example_kwarg example_value`)."
        )

    return kwargs_cleaned


@workflows_app.command()
def explore():
    """
    interactively view all available workflows to see docs & paramaters
    available
    """

    # when printing statements, we often want to add this to the start of the
    # string, so we save this up front
    prefix = "\n\n[bold green]"

    from simmate.workflows.utilities import (
        get_list_of_workflows_by_type,
        get_workflow,
        get_workflow_types,
    )

    print(f"{prefix}What type of analysis are you interested in?")
    workflow_types = get_workflow_types()
    type_index = list_options(workflow_types)
    selected_type = workflow_types[type_index]

    # TODO: have the user select a calculator for this analysis. For now,
    # we are assuming VASP because those are our only workflows

    print(f"{prefix}What settings preset do you want to see the description for?")
    presets = get_list_of_workflows_by_type(selected_type, full_name=False)
    present_index = list_options(presets)
    selected_preset = presets[present_index]

    final_workflow_name = selected_type + ".vasp." + selected_preset
    # BUG: I assume vasp for now, but this should change when I add workflows
    # from new calculators.

    print(f"{prefix}===================== {final_workflow_name} =====================")

    # now we load this workflow and print the docstring.
    workflow = get_workflow(
        workflow_name=final_workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )

    # extra import in order to render markdown in the terminal
    # from: https://rich.readthedocs.io/en/stable/markdown.html
    # Docstrings often have the entire string indented a number of times.
    # We need to strip those idents away to render properly. This is the dedent.
    from textwrap import dedent

    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()

    print(f"{prefix}Description:\n")
    description = Markdown(dedent(workflow.__doc__))
    console.print(description)

    print(f"{prefix}Parameters:\n")
    workflow.show_parameters()

    endnote = Markdown(
        "To understand each parameter, you can read through "
        "[our parameter docs](https://jacksund.github.io/simmate/parameters/)"
        ", which give full descriptions and examples."
    )
    console.print(endnote)

    print(f"{prefix}==================================================================")


@workflows_app.command()
def list_all():
    """
    This lists off all available workflows.
    """

    from simmate.workflows.utilities import get_list_of_all_workflows

    print("These are the workflows that have been registerd:")
    all_workflows = get_list_of_all_workflows()
    for i, workflow in enumerate(all_workflows):
        workflow_number = str(i + 1).zfill(2)
        print(f"\t({workflow_number}) {workflow}")  # gives "(01) example-flow"


@workflows_app.command()
def show_config(workflow_name: str):
    """
    The calculation's configuration settings are displayed

    For example, a VASP workflow will show a dictionary that details how
    INCAR settings are selected.
    """

    from simmate.workflows.utilities import get_workflow

    workflow = get_workflow(
        workflow_name=workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )

    workflow.show_config()


@workflows_app.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
def setup_only(context: Context, workflow_name: str):
    """
    the calculation is set up but not ran (S3Workflows only)

    This is useful when you just want the input files to view/edit.
    """

    from simmate.workflows.utilities import get_workflow

    workflow = get_workflow(
        workflow_name=workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )
    kwargs_input = parse_parameters(context=context)
    kwargs_cleaned = workflow._deserialize_parameters(**kwargs_input)

    # if no folder was given, just name it after the workflow. We also replace
    # spaces with underscores
    from simmate.utilities import get_directory

    directory = kwargs_cleaned.get("directory", None)
    if not directory:
        directory = f"{workflow.name_full}.SETUP-ONLY"

    # ensure a path obj and that directory is created
    kwargs_cleaned["directory"] = get_directory(directory)

    logging.info("Writing inputs")

    # Not all workflows have a single input because some are NestWorkflows,
    # meaning they are made of multiple smaller workflows.
    from simmate.workflow_engine import S3Workflow

    if issubclass(workflow, S3Workflow):

        workflow.setup(**kwargs_cleaned)
    else:
        raise typer.BadParameter(
            "This is not a S3-based workflow. It is likely a NestedWorkflow, "
            "meaning it is made up of multiple smaller workflows. We have not "
            "added a setup-only feature for these yet. "
        )

    logging.info(f"Done! Your input files are located in {directory}")


@workflows_app.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
def run_quick(context: Context, workflow_name: str):
    """Runs a workflow using provided parameters as CLI arguments"""

    from simmate.workflows.utilities import get_workflow

    workflow = get_workflow(
        workflow_name=workflow_name,
        precheck_flow_exists=True,
        print_equivalent_import=True,
    )
    kwargs_cleaned = parse_parameters(context=context)

    result = workflow.run(**kwargs_cleaned)

    # Let the user know everything succeeded
    if result.is_completed():
        logging.info("Success! All results are also stored in your database.")


@workflows_app.command()
def run(filename: Path):
    """Runs a workflow locally where parameters are loaded from a yaml file"""

    import yaml

    with filename.open() as file:
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

    workflow.run(**parameters).result()


@workflows_app.command()
def run_cloud(filename: Path):
    """
    Submits a workflow to cloud for remote running where parameters are loaded
    from a yaml file
    """
    # !!! DEV NOTE: This is a copy/paste of the run() command. Condense these
    # when refactoring

    import yaml

    with filename.open() as file:
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

    workflow.run_cloud(**parameters)
