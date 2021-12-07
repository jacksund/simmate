# -*- coding: utf-8 -*-

import click


@click.group()
def workflows():
    """A group of commands for running common workflows."""
    pass


@workflows.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "--vasp_command",
    "-c",
    default="vasp > vasp.out",
    help="the command used to call VASP (e.g. 'mpirun -n 12 vasp > vasp.out')",
)
@click.option(
    "--directory",
    "-d",
    default=None,
    help="the folder to run this workflow in",
)
def mit_relaxation(filename, vasp_command, directory):
    """Runs a VASP geometry relaxation using MIT Project settings."""

    # click.echo(click.format_filename(filename))
    click.echo("LOADING STRUCTURE...")
    from pymatgen.core.structure import Structure

    structure = Structure.from_file(filename)

    click.echo("LOADING WORKFLOW...")
    from simmate.workflows.relaxation.mit import workflow

    click.echo("RUNNING WORKFLOW...")
    result = workflow.run(
        structure=structure,
        directory=directory,
        vasp_command=vasp_command,
    )

    # Let the user know everything succeeded
    if result.is_successful():
        click.echo("Success! All results are also stored in your database.")
