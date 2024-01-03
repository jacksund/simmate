# -*- coding: utf-8 -*-

import typer

setup_app = typer.Typer(rich_markup_mode="markdown")


@setup_app.callback(no_args_is_help=True)
def setup():
    """
    A group of commands for configuring QE and PWscf
    """
    pass


@setup_app.command()
def docker():
    """
    Adds `use_docker: true` to Simmate's QE settings
    """
    from simmate.apps.quantum_espresso.settings import setup_docker

    setup_docker()


@setup_app.command()
def sssp():
    """
    Downloads and configures potentials from SSSP
    """
    from simmate.apps.quantum_espresso.inputs.potentials_sssp import setup_sssp

    setup_sssp()
