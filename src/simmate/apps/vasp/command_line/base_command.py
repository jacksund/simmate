# -*- coding: utf-8 -*-

"""
This defines the base "simmate-vasp" command that all other commands stem from.
"""

import typer

from simmate.apps.vasp.command_line.inputs import inputs_app
from simmate.apps.vasp.command_line.plot import plot_app

vasp_app = typer.Typer(rich_markup_mode="markdown")


@vasp_app.callback(no_args_is_help=True)
def base_command():
    """
    A collection of utilities to help work with VASP
    """
    # When we call the command "simmate-vasp" this is where we start, and it then
    # looks for all other functions that have the decorator "@simmate_vasp.command()"
    # to decide what to do from there.
    pass


# All commands are organized into other files, so we need to manually register
# them to our base "simmate-vasp" command here.
vasp_app.add_typer(inputs_app, name="inputs")
vasp_app.add_typer(plot_app, name="plot")
