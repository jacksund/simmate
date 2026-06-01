# -*- coding: utf-8 -*-

import typer

setup_app = typer.Typer(rich_markup_mode="markdown")


@setup_app.callback(no_args_is_help=True)
def setup():
    """
    Commands for configuring Quantum Espresso, including potential libraries
    (SSSP).
    """
    pass


@setup_app.command()
def sssp():
    """
    Downloads and configures the Standard Solid State Pseudopotentials (SSSP) library.
    """
    from ..inputs import setup_sssp

    setup_sssp()
