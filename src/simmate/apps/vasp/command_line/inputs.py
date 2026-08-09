# -*- coding: utf-8 -*-

from pathlib import Path

import typer

inputs_app = typer.Typer(rich_markup_mode="markdown")


@inputs_app.callback(no_args_is_help=True)
def inputs():
    """
    Commands for generating and analyzing VASP input files (POTCAR, INCAR, etc.).
    """
    pass


@inputs_app.command()
def get_potcar(
    elements: list[str] = typer.Argument(
        ...,
        help="The list of elements to fetch POTCAR files for (e.g., 'Y', 'C', 'F').",
    ),
    functional: str = typer.Option(
        "PBE",
        help="The VASP functional type (e.g., 'PBE', 'LDA').",
    ),
    combine: bool = typer.Option(
        False,
        help="Whether to combine individual POTCAR files into a single master POTCAR.",
    ),
):
    """
    Retrieves and saves POTCAR files for the specified elements and functional.
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
def compare_incars(
    incar1: Path = typer.Argument(
        ...,
        help="The path to the first INCAR file.",
    ),
    incar2: Path = typer.Argument(
        ...,
        help="The path to the second INCAR file.",
    ),
):
    """
    Compares two INCAR files and displays similarities and differences in YAML format.
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
