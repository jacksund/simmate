# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.bader.workflows import (
    PopulationAnalysis__Bader__Bader,
    PopulationAnalysis__Bader__CombineChgcars,
)
from simmate.apps.materials_project.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)
from simmate.engine import Workflow
from simmate.toolkit import Structure
from simmate.utilities import copy_files_from_directory


class PopulationAnalysis__VaspBader__BaderMatproj(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density.
    """

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        **kwargs,
    ):
        prebader_dir = directory / StaticEnergy__Vasp__PrebaderMatproj.name_full
        StaticEnergy__Vasp__PrebaderMatproj.run(
            structure=structure,
            command=command,
            source=source,
            directory=prebader_dir,
        ).result()

        # Setup chargecars for the bader analysis and wait until complete
        chgcomb_dir = directory / PopulationAnalysis__Bader__CombineChgcars.name_full
        PopulationAnalysis__Bader__CombineChgcars.run(
            directory=chgcomb_dir,
            previous_directory=prebader_dir,
        ).result()

        # And run the bader analysis on the resulting chg denisty
        bader_dir = directory / PopulationAnalysis__Bader__Bader.name_full
        PopulationAnalysis__Bader__Bader.run(
            directory=bader_dir,
            previous_directory=chgcomb_dir,
        ).result()

        # The from_vasp_directory method that loads results into the database
        # requires the following files to be in the main directory:
        #  1. the ACF.dat
        #  2. INCAR
        #  3. vasprun.xml
        #  4. POTCAR
        #  5. CHGCAR
        copy_files_from_directory(
            files_to_copy=["ACF.dat"],
            directory_new=directory,
            directory_old=bader_dir,
        )
        copy_files_from_directory(
            files_to_copy=["INCAR", "vasprun.xml", "POTCAR", "CHGCAR"],
            directory_new=directory,
            directory_old=prebader_dir,
        )
        # !!! I need a better way to access these files in the workup method
        # without copying them into the main dir...


class StaticEnergy__Vasp__PrebaderMatproj(StaticEnergy__Vasp__Matproj):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Materials Project. Results can be used for Bader analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.

    See `bader.workflows.materials_project`.
    """

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    _incar_updates = dict(
        NGXF__density_a=20,
        NGYF__density_b=20,
        NGZF__density_c=20,
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
    )
