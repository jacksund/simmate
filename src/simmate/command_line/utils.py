# -*- coding: utf-8 -*-

"""
This defines utility commands for miscellaneous tasks like file management.
All commands are accessible through the "simmate utils" command.
"""

from pathlib import Path

import typer

utils_app = typer.Typer(rich_markup_mode="markdown")


@utils_app.callback(no_args_is_help=True)
def utils():
    """
    Miscellaneous utility commands for Simmate (e.g., file management and archiving).
    """
    pass


@utils_app.command()
def archive_old_runs(
    directory: Path = typer.Option(
        Path.cwd(),
        help="The directory to search for old simulation folders.",
    ),
    time_cutoff: float = typer.Option(
        3 * 7 * 24 * 60 * 60,  # equal to 3 weeks
        help="The minimum age (in seconds) of a folder before it is considered 'old' and archived. Defaults to 3 weeks.",
    ),
):
    """
    Compresses old simulation folders (matching `simmate-task-*`) into ZIP archives.

    This helps keep your project directory clean while preserving data from
    older runs.
    """

    from simmate.utils import archive_old_runs

    archive_old_runs(directory, time_cutoff)
