# -*- coding: utf-8 -*-

from pathlib import Path

import typer

inputs_app = typer.Typer(rich_markup_mode="markdown")


@inputs_app.callback(no_args_is_help=True)
def inputs():
    """
    A group of commands for creating VASP inputs
    """
    pass


@inputs_app.command()
def get_potcar(elements: list[str], potential: str = "PBE", combine: bool = False):
    """
    Grabs the POTCAR file(s) of the requested type

    ex: `simmate-vasp inputs get-potcar Y C F`
    """
    raise NotImplementedError("This command is still under testing")


@inputs_app.command()
def compare_incars(incar1: Path, incar2: Path):
    """
    Compares settings between two INCAR files and shows their results
    """
    raise NotImplementedError("This command is still under testing")
