# -*- coding: utf-8 -*-

from pathlib import Path

import typer

plot_app = typer.Typer(rich_markup_mode="markdown")


@plot_app.callback(no_args_is_help=True)
def plot():
    """
    A group of commands for plotting results from VASP outputs
    """
    pass


@plot_app.command()
def band_structure(directory: Path = Path.cwd()):
    """
    Plot the band structure using the vasprun.xml output file
    """
    raise NotImplementedError("This command is still under testing")


@plot_app.command()
def neb_diffusion(directory: Path = Path.cwd()):
    """
    Plot the NEB diffusion barrier using the vasprun.xml output file
    """
    raise NotImplementedError("This command is still under testing")


@plot_app.command()
def density_of_states(directory: Path = Path.cwd()):
    """
    Plot the density of states using the vasprun.xml output file
    """
    raise NotImplementedError("This command is still under testing")


@plot_app.command()
def relaxation(directory: Path = Path.cwd()):
    """
    Plot the relaxation convergence using the vasprun.xml output file
    """
    raise NotImplementedError("This command is still under testing")
