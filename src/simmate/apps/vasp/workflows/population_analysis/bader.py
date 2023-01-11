# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.bader.workflows import (
    PopulationAnalysis__Bader__Bader,
    PopulationAnalysis__Bader__CombineChgcars,
)
from simmate.calculators.vasp.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)
from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow


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

        prebader_result = StaticEnergy__Vasp__PrebaderMatproj.run(
            structure=structure,
            command=command,
            source=source,
            directory=directory,
        ).result()

        # Setup chargecars for the bader analysis and wait until complete
        PopulationAnalysis__Bader__CombineChgcars.run(
            directory=prebader_result.directory,
        ).result()

        # Bader only adds files and doesn't overwrite any, so I just run it
        # in the original directory. I may switch to copying over to a new
        # directory in the future though.
        PopulationAnalysis__Bader__Bader.run(
            directory=prebader_result.directory,
        ).result()


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
    incar = StaticEnergy__Vasp__Matproj.incar.copy()
    incar.update(
        NGXF__density_a=20,
        NGYF__density_b=20,
        NGZF__density_c=20,
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
    )
