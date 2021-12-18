# -*- coding: utf-8 -*-

import click


@click.group()
def workflows():
    """A group of commands for running workflows or viewing their settings."""
    pass


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

    raise click.ClickException("This feature hasn't been implemented yet, sorry!")


@workflows.command()
@click.argument("workflow_name")
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "--directory",
    "-d",
    default=None,
    help="the folder to write input file in. Defaults to simmate-task-12345, where 12345 is randomized",
)
def setup_only(filename, vasp_command, directory):
    """
    If the workflow is a single task, the calculation is set up but not ran. This
    is useful when you just want the input files to view/edit.
    """

    raise click.ClickException("This feature hasn't been implemented yet, sorry!")


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
    from simmate.workflows import all as all_workflows
    from simmate.workflows.utilities import get_list_of_all_workflows
    from pymatgen.core.structure import Structure

    allowed_workflows = get_list_of_all_workflows()

    # make sure we have a proper workflow name provided
    if workflow_name not in allowed_workflows:
        raise click.ClickException(
            "The workflow you provided isn't known. Make sure you don't have any "
            "typos! If you want a list of all available workflows, use the command "
            " 'simmate workflows list-all'"
        )
    workflow = getattr(all_workflows, workflow_name)

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
