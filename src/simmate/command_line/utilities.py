# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate workflow engine. All commands are 
accessible through the "simmate workflow-engine" command.
"""

from pathlib import Path

import typer

utilities_app = typer.Typer(rich_markup_mode="markdown")


@utilities_app.callback(no_args_is_help=True)
def utilities():
    """
    A group of commands for various simple tasks (such as file handling)
    """
    pass


@utilities_app.command()
def archive_old_runs(
    directory: Path = Path.cwd(),
    time_cutoff: float = 3 * 7 * 24 * 60 * 60,  # equal to 3 weeks
):
    """
    Compresses old simmate-task-* folders to zip files

    - `directory`: the folder to search for old runs

    - `time_cutoff`: the time (in seconds) that a folder hasn't been editted in
    order to consider the run "old"
    """

    from simmate.utilities import archive_old_runs

    archive_old_runs(directory, time_cutoff)
