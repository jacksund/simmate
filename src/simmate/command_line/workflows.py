# -*- coding: utf-8 -*-

import click


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
        Name of the workflow to grab
    """
    from simmate.workflows import all as all_workflows
    from simmate.workflows.utilities import get_list_of_all_workflows

    allowed_workflows = get_list_of_all_workflows()

    # make sure we have a proper workflow name provided
    if workflow_name not in allowed_workflows:
        raise click.ClickException(
            "The workflow you provided isn't known. Make sure you don't have any "
            "typos! If you want a list of all available workflows, use the command "
            " 'simmate workflows list-all'"
        )
    workflow = getattr(all_workflows, workflow_name)
    return workflow


@workflows.command()
def list_all():
    """
    This lists off all available workflows.
    """

    click.echo("Gathering all available workflows...")

    from simmate.workflows.utilities import get_list_of_all_workflows

    click.echo("These are all workflows you can use:")
    all_workflows = get_list_of_all_workflows()
    for i, workflow in enumerate(all_workflows):
        click.echo(f"\t({i+1}) {workflow}")  # gives "(1) example_flow"


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
    from pymatgen.core.structure import Structure

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


@workflows.command()
@click.argument("workflow_name")
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "--command",
    "-c",
    default=None,
    help="the command used to call call the calculator (e.g. 'mpirun -n 12 vasp > vasp.out')",
)
@click.option(
    "--directory",
    "-d",
    default=None,
    help="the folder to run this workflow in. Defaults to simmate-task-12345, where 12345 is randomized",
)
@click.option(
    "--local",
    "-l",
    default=False,
    help="whether to run this flow locally. if false, it will be scheduled on prefect cloud",
)
def run(workflow_name, filename, command, directory):
    """Runs a workflow using an input structure file"""

    click.echo("LOADING STRUCTURE AND WORKFLOW...")
    from pymatgen.core.structure import Structure

    workflow = get_workflow(workflow_name)
    structure = Structure.from_file(filename)

    click.echo("RUNNING WORKFLOW...")

    # we don't want to pass command=None if the user didn't provide one. Instead
    # we want the workflow to use its own default value. To do this, we pass
    # the command input as a kwarg -- or an empty dict if it wasn't given.
    command_kwargs = {"command": command} if command else {}

    result = workflow.run(
        structure=structure,
        directory=directory,
        **command_kwargs,
    )

    # Let the user know everything succeeded
    if result.is_successful():
        click.echo("Success! All results are also stored in your database.")
