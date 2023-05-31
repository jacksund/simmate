# -*- coding: utf-8 -*-

from pathlib import Path

import typer

inputs_app = typer.Typer(rich_markup_mode="markdown")


@inputs_app.callback(no_args_is_help=True)
def inputs():
    """
    A group of commands for creating and analyzing VASP inputs
    """
    pass


@inputs_app.command()
def get_potcar(elements: list[str], functional: str = "PBE", combine: bool = False):
    """
    Grabs the POTCAR file(s) of the requested type

    ex: `simmate-vasp inputs get-potcar Y C F`
    """
    from pymatgen.core import Element

    from simmate.apps.vasp.inputs import Potcar

    elements = [Element(e) for e in elements]
    for element in elements:
        Potcar.to_file_from_type(
            elements=[element],
            functional=functional,
            filename=f"POTCAR_{element}",
        )

    if combine and len(elements) > 1:
        Potcar.to_file_from_type(elements, functional)


@inputs_app.command()
def compare_incars(incar1: Path, incar2: Path):
    """
    Compares settings between two INCAR files and shows their similarities and
    differences
    """
    import yaml

    from simmate.apps.vasp.inputs import Incar

    incar1 = Incar.from_file(filename=incar1)
    incar2 = Incar.from_file(filename=incar2)

    result = incar1.compare_incars(incar2)

    # BUG-FIX: Tuples print ugly, so we convert them to a list
    for key, value in result["Different"].items():
        if isinstance(value, tuple):
            result["Different"][key] = list(value)

    print(yaml.dump(result))
