# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate workflow engine. All commands are 
accessible through the "simmate workflow-engine" command.
"""

import pathlib

import click


@click.group()
def utilities():
    """
    A group of commands for various simple tasks - such as file handling.
    """
    pass


@utilities.command()
@click.argument(
    "directory",
    default=pathlib.Path.cwd(),
    type=click.Path(exists=True, path_type=pathlib.Path),
)
@click.option(
    "--time_cutoff",
    "-t",
    default=3 * 7 * 24 * 60 * 60,  # equal to 3 weeks
    type=float,
    help=(
        "if the queue is empty, the time (in seconds) the worker should wait"
        " before checking the queue again"
    ),
)
def archive_old_runs(directory, time_cutoff):
    """
    This starts a Simmate Worker which will query the database for jobs to run.
    """

    from simmate.utilities import archive_old_runs

    archive_old_runs(directory, time_cutoff)


# explicitly list functions so that pdoc doesn't skip them
__all__ = [
    "archive_old_runs",
]
