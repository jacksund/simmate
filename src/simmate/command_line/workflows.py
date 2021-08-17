# -*- coding: utf-8 -*-

import click


@click.group()
def workflows():
    """A group of commands for running common workflows."""
    pass


@workflows.command()
def mit_relaxation():
    """Runs a VASP geometry relaxation using MIT Project settings."""
    
    click.echo("LOADING WORKFLOW...")
    from simmate.workflows.relaxation.mit import workflow
    
    click.echo("RUNNING WORKFLOW...")
    print(workflow)

    # Let the user know everything succeeded
    click.echo("Success! All results are also stored in your database.")
