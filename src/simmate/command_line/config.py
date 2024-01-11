# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate configuration settings. All commands are 
accessible through the "simmate config" command.
"""

from pathlib import Path

import typer

config_app = typer.Typer(rich_markup_mode="markdown")


@config_app.callback(no_args_is_help=True)
def utilities():
    """
    A group of commands for managing Simmate settings
    """
    pass


@config_app.command()
def write(filename: Path = None):
    """
    Writes the final simmate settings to yaml file

    - `filename`: file name to write settings to
    """

    from simmate.configuration import settings

    settings.write_settings(filename=filename)


@config_app.command()
def show(user_only: bool = False):
    """
    Takes the final simmate settings and prints them in a yaml format that is
    easier to read.
    """
    from simmate.configuration import settings

    settings.show_settings(user_only=user_only)
