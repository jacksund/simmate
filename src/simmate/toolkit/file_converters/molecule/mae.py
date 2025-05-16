# -*- coding: utf-8 -*-

from pathlib import Path

from rdkit.Chem.rdmolfiles import MaeMolSupplier, MaeWriter
from rich.progress import track

from simmate.toolkit import Molecule


class MaeAdapter:
    """
    Read and writes molecules from Schrodinger's `.mae` file format into Simmate
    Molecule objects.

    This is a wrapper around RDKit's MaeMolSupplier and MaeWriter classes.
    See RDKit docs at...
    - https://www.rdkit.org/docs/source/rdkit.Chem.rdmolfiles.html#rdkit.Chem.rdmolfiles.MaeMolSupplier
    - https://www.rdkit.org/docs/source/rdkit.Chem.rdmolfiles.html#rdkit.Chem.rdmolfiles.MaeWriter
    """

    @staticmethod
    def get_toolkits_from_file(
        filename: Path | str,  # e.g. "in.mae"
        skip_failed: bool = False,
        file_open_kwargs: dict = {},
        **kwargs,
    ) -> list[Molecule]:
        # this is the code for Molecule.from_mae_file() method

        filename = Path(filename)
        with filename.open("r", **file_open_kwargs) as file:

            supplier = MaeMolSupplier(file)  # file() function...?
            # TODO: support compressed
            # import gzip
            # suppl = MaeMolSupplier(gzip.open('in.maegz'))

            molecules = []
            for molecule in supplier:
                if molecule is not None:
                    molecules.append(molecule)
                elif not skip_failed:
                    raise Exception("Error loading molecule within '.mae' file")

        return molecules if len(molecules) > 1 else molecules[0]

    @staticmethod
    def to_file_from_toolkits(
        molecules: list[Molecule],
        filename: Path | str,
        **kwargs,
    ):

        # OPTIMIZE: use file.open context...?
        filename = Path(filename)
        writer = MaeWriter(filename)
        for molecule in track(molecules):
            writer.write(molecule.rdkit_molecule)
