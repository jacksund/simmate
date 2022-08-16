# -*- coding: utf-8 -*-

from pathlib import Path

from pymatgen.io.vasp.outputs import Chgcar, Elfcar

from simmate.toolkit import Structure

from .bader import PopulationAnalysis__Bader__Bader


class PopulationAnalysis__Bader__Badelf(PopulationAnalysis__Bader__Bader):
    """
    Runs Bader analysis where the ELFCAR is used as the partitioning reference
    instead of CHGCAR.
    """

    command = "bader CHGCAR_empty -ref ELFCAR_empty > bader.out"
    required_files = ["CHGCAR", "ELFCAR"]
    use_database = False

    @staticmethod
    def setup(structure: Structure, directory: Path):
        """
        Bader analysis requires that a static-energy calculation be ran beforehand
        - typically using VASP. This setup involves ensuring that
        the proper files are present. In addition, it creates new CHGCAR and
        ELFCAR files with an update structure -- typically containing empty atoms.

        #### Parameters

        - `structure`:
            The structure to use when rewriting the ELFCAR and CHGCAR files.
        """

        # establish file names
        elfcar_filename = directory / "ELFCAR"
        chgcar_filename = directory / "CHGCAR"

        # Load ELFCAR + CHGCAR and replace the structure with the one we created that includes
        # empty atoms.
        elfcar = Elfcar.from_file(elfcar_filename)
        elfcar.structure = structure  # replaces the original structure in file
        elfcar.write_file(f"{elfcar_filename}_empty")
        chgcar = Chgcar.from_file(chgcar_filename)
        chgcar.structure = structure  # replaces the original structure in file
        chgcar.write_file(f"{chgcar_filename}_empty")
