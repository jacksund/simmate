# -*- coding: utf-8 -*-

"""
This defines the base "simmate-badelf" command that all other commands stem from.
"""

import logging
from pathlib import Path

import typer
from typer import Context

from simmate.apps.warren_lab.workflows.badelf.badelf import (
    BadElfAnalysis__Badelf__Badelf,
)
from simmate.command_line.workflows import parse_parameters

badelf_app = typer.Typer(rich_markup_mode="markdown")


@badelf_app.callback(no_args_is_help=True)
def base_command():
    """
    A collection of utilities to help work with VASP
    """
    # When we call the command "badelf-vasp" this is where we start, and it then
    # looks for all other functions that have the decorator "@badelf_vasp.command()"
    # to decide what to do from there.
    pass


@badelf_app.command()
def run(
    context: Context,
    directory: Path = typer.Option(
        Path("."), help="Path to the directory with VASP files"
    ),  # we default to the current directory
    cores: int = typer.Option(
        None,
        help="The number of cores (NOT threads) to parallelize voxel assignment across. Will default to 90% of available cores.",
    ),
    find_electrides: bool = typer.Option(
        True, help="Whether or not the algorithm will search for electride sites"
    ),
    min_elf: float = typer.Option(
        0.5, help="The minimum ELF cutoff for a site to be considered an electride"
    ),  # This is somewhat arbitrarily set
    algorithm: str = typer.Option("badelf", help="The algorithm used for partitioning"),
    elf_connection_cutoff: float = typer.Option(
        0, help="The ELF cutoff when checking for electride dimensionality"
    ),
    check_for_covalency: bool = typer.Option(
        True,
        help="Whether to stop the calculation if covalency is detected. Highly recommended.",
    ),
):
    """A command for running BadELF analysis"""

    # If no directory is specified, assume the user wishes to run in the current
    # directory
    kwargs_cleaned = parse_parameters(context=context)

    result = BadElfAnalysis__Badelf__Badelf().run(
        directory=directory,
        cores=cores,
        find_electrides=find_electrides,
        min_elf=min_elf,
        algorithm=algorithm,
        elf_connection_cutoff=elf_connection_cutoff,
        check_for_covalency=check_for_covalency,
        **kwargs_cleaned,
    )

    # Let the user know everything succeeded
    if result.is_completed():
        logging.info("Success! All results are also stored in your database.")
