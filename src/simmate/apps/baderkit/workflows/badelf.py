# -*- coding: utf-8 -*-

import os
from pathlib import Path

from baderkit import Grid
from baderkit.elf_analysis import Badelf
from baderkit.elf_analysis.elf_labeler.enum_and_styling import FeatureType

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
        # create CHGCAR_sum grid
        grid1 = Grid.from_vasp(directory / "AECCAR0")
        grid2 = Grid.from_vasp(directory / "AECCAR2")
        total_charge_grid = grid1.linear_add(grid2)

        # Get the badelf toolkit object for running badelf.
        badelf = cls.badelf_class.from_vasp(
            charge_filename=directory / "CHGCAR",
            reference_filename=directory / "ELFCAR",
            total_charge_grid=total_charge_grid,
            pseudopotential_filename=directory / "POTCAR",
            **kwargs,
        )
        # update database
        analysis_datatable = cls.database_table.objects.get(run_id=run_id)
        analysis_datatable.update_from_badelf(
            badelf=badelf, directory=directory, **kwargs
        )

        # write results
        badelf.write_species_volume(
            species=FeatureType.nna,
            filename=directory / "ELFCAR_e"
            )
        badelf.nna_structure.to(directory / "POSCAR_e", "POSCAR")

        badelf.write_json(
            directory / "badelf.json"
        )

        # remove the ELFCAR, CHGCAR, and POTCAR copies for space
        for file in cls.use_previous_directory:
            os.remove(directory / file)
            
class SpinBadelfBase(Workflow):
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
        charge_grid = Grid.from_vasp(directory/"CHGCAR", total_only=False)
        elf_grid = Grid.from_vasp(directory/"ELFCAR", total_only=False)
        
        charge_grid_up, charge_grid_down = charge_grid.split_to_spin()
        elf_grid_up, elf_grid_down = elf_grid.split_to_spin()
        
        # Get the badelf toolkit object for running badelf.
        badelf_up = cls.badelf_class.from_vasp(
            charge_grid=charge_grid_up,
            reference_grid=elf_grid_up,
            pseudopotential_filename=directory / "POTCAR",
            **kwargs,
        )
        badelf_up.spin_system = "up"
        badelf_down = cls.badelf_class.from_vasp(
            charge_grid=charge_grid_down,
            reference_grid=elf_grid_down,
            pseudopotential_filename=directory / "POTCAR",
            **kwargs,
        )
        badelf_up.spin_system = "down"
        # update database
        analysis_datatable = cls.database_table.objects.get(run_id=run_id)
        analysis_datatable.update_from_badelf(
            badelf=badelf_up, directory=directory, **kwargs
        )
        analysis_datatable.update_from_badelf(
            badelf=badelf_down, directory=directory, **kwargs
        )

        # write results
        badelf_up.write_species_volume(
            species=FeatureType.nna,
            filename=directory / "ELFCAR_up_e"
            )
        badelf_down.write_species_volume(
            species=FeatureType.nna,
            filename=directory / "ELFCAR_down_e"
            )
        badelf_up.nna_structure.to(directory / "POSCAR_up_e", "POSCAR")
        badelf_down.nna_structure.to(directory / "POSCAR_down_e", "POSCAR")

        badelf_up.write_json(
            directory / "badelf_up.json"
        )
        badelf_down.write_json(
            directory / "badelf_down.json"
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

class Badelf__Baderkit__SpinBadelf(SpinBadelfBase):
    """
    Runs a Bader and BadELF analysis without running a static
    energy calculation. The directory must already have an
    ELFCAR and CHGCAR with the same grid size as well as the AECCAR0 and
    AECCAR2 files.

    This method assumes the calculation WAS spin dependent.
    """

    badelf_class = Badelf
    use_database = True
    database_table = BadelfModel

