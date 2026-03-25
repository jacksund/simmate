# -*- coding: utf-8 -*-

"""
This defines the base "simmate-qe" command that all other commands stem from.
"""

import typer

from simmate.apps.quantum_espresso.command_line.setup import setup_app

qe_app = typer.Typer(
    rich_markup_mode="markdown",
    add_completion=False,
)


@qe_app.callback(no_args_is_help=True)
def base_command():
    """
    Commands and utilities for managing Quantum Espresso (QE) calculations
    and configurations.
    """
    pass


# All commands are organized into other files, so we need to manually register
# them to our base "simmate-qe" command here.
qe_app.add_typer(setup_app, name="setup")
