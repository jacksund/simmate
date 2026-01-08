# -*- coding: utf-8 -*-

import os
from pathlib import Path

from baderkit.core import Badelf, SpinBadelf

from simmate.apps.baderkit.models import BadelfCalculation as BadelfModel
from simmate.apps.baderkit.models import SpinBadelfCalculation as SpinBadelfModel
from simmate.database import connect
from simmate.workflows import Workflow


class BadelfBase(Workflow):
    """
    This is the base class that builds out the BadELF workflow. It should
    not be run directly, but inherited from.
    """

    required_files = ["CHGCAR", "ELFCAR", "POTCAR"]
    use_previous_directory = ["CHGCAR", "ELFCAR", "POTCAR"]
    use_database = False
    badelf_class = None

    @classmethod
    def run_config(
        cls,
        source: dict = None,
        directory: Path = None,
        run_id: str = None,
        **kwargs,
    ):

        # Get the badelf toolkit object for running badelf.
        badelf_tools = cls.badelf_class.from_vasp(
            charge_file=directory / "CHGCAR",
            reference_file=directory / "ELFCAR",
            **kwargs,
        )
        # update database
        analysis_datatable = cls.database_table.objects.get(run_id=run_id)
        analysis_datatable.update_from_badelf(
            badelf=badelf_tools, directory=directory, **kwargs
        )

        # write results
        badelf_tools.write_species_volume(directory=directory)
        # badelf_tools.write_species_volume(directory=directory, write_reference=False)
        badelf_tools.labeled_structure.to(directory / "POSCAR_labeled", "POSCAR")
        badelf_tools.electride_structure.to(directory / "POSCAR_e", "POSCAR")

        badelf_tools.write_json(
            directory / "badelf.json", potcar_path=directory / "POTCAR"
        )

        # remove the ELFCAR, CHGCAR, and POTCAR copies for space
        for file in cls.use_previous_directory:
            os.remove(directory / file)


class Badelf__Baderkit__Badelf(BadelfBase):
    """
    Runs a Bader and BadELF analysis without running a static
    energy calculation. The directory must already have an
    ELFCAR and CHGCAR with the same grid size as well as the AECCAR0 and
    AECCAR2 files.

    This method assumes the calculation was NOT spin dependent.
    """

    badelf_class = Badelf
    use_database = True
    database_table = BadelfModel


class Badelf__Baderkit__SpinBadelf(BadelfBase):
    """
    Runs a Bader and BadELF analysis without running a static
    energy calculation. The directory must already have an
    ELFCAR and CHGCAR with the same grid size as well as the AECCAR0 and
    AECCAR2 files.

    This method assumes the calculation WAS spin dependent.
    """

    badelf_class = SpinBadelf
    use_database = True
    database_table = SpinBadelfModel
