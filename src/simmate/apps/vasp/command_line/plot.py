# -*- coding: utf-8 -*-

from pathlib import Path

import typer

plot_app = typer.Typer(rich_markup_mode="markdown")


@plot_app.callback(no_args_is_help=True)
def plot():
    """
    Commands for visualizing VASP output data (band structures, DOS, etc.).
    """
    pass


@plot_app.command()
def band_structure(
    directory: Path = typer.Option(
        Path.cwd(),
        help="The directory containing the `vasprun.xml` file.",
    )
):
    """
    Generates a band structure plot from VASP output.
    """
    raise NotImplementedError("This command is still under testing")


@plot_app.command()
def neb_diffusion(
    directory: Path = typer.Option(
        Path.cwd(),
        help="The directory containing the NEB calculation folders.",
    )
):
    """
    Generates an NEB diffusion barrier plot from VASP output.
    """
    raise NotImplementedError("This command is still under testing")


@plot_app.command()
def density_of_states(
    directory: Path = typer.Option(
        Path.cwd(),
        help="The directory containing the `vasprun.xml` file.",
    )
):
    """
    Generates a density of states (DOS) plot from VASP output.
    """
    raise NotImplementedError("This command is still under testing")


@plot_app.command()
def relaxation(
    directory: Path = typer.Option(
        Path.cwd(),
        help="The directory containing the `vasprun.xml` file.",
    )
):
    """
    Generates a relaxation convergence plot from VASP output.
    """
    raise NotImplementedError("This command is still under testing")
