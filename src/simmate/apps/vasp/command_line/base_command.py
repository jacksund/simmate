# -*- coding: utf-8 -*-

"""
This defines the base "simmate-vasp" command that all other commands stem from.
"""

import typer

from simmate.apps.vasp.command_line.inputs import inputs_app
from simmate.apps.vasp.command_line.plot import plot_app

vasp_app = typer.Typer(
    rich_markup_mode="markdown",
    add_completion=False,
)


@vasp_app.callback(no_args_is_help=True)
def base_command():
    """
    Commands and utilities for managing VASP calculations, input files,
    and output visualizations.
    """
    pass


# All commands are organized into other files, so we need to manually register
# them to our base "simmate-vasp" command here.
vasp_app.add_typer(inputs_app, name="inputs")
vasp_app.add_typer(plot_app, name="plot")
