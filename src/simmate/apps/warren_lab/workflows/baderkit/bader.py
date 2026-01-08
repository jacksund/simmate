# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.baderkit.workflows import Bader__Baderkit__Bader
from simmate.apps.vasp.inputs.potcar_mappings import PBE_GW_POTCAR_MAPPINGS
from simmate.apps.warren_lab.workflows.static_energy import (
    StaticEnergy__Vasp__PbesolWarren,
)
from simmate.toolkit import Structure
from simmate.workflows import Workflow


class Bader__VaspBaderkit__BaderWarren(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density.
    """

    use_database = False  # nested workflows save separately

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        source: dict = None,
        directory: Path = None,
        subworkflow_kwargs: dict = {},
        **kwargs,
    ):
        prebader_dir = directory / StaticEnergy__Vasp__PrebaderWarren.name_full
        result = StaticEnergy__Vasp__PrebaderWarren.run(
            structure=structure,
            source=source,
            directory=prebader_dir,
            **subworkflow_kwargs,
        ).result()

        # And run the bader analysis on the resulting chg denisty
        bader_dir = directory / Bader__Baderkit__Bader.name_full
        Bader__Baderkit__Bader.run(
            directory=bader_dir,
            previous_directory=prebader_dir,
            source=result,
            **subworkflow_kwargs,
        ).result()


class StaticEnergy__Vasp__PrebaderWarren(StaticEnergy__Vasp__PbesolWarren):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Warren Lab. Results can be used for Bader analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.

    """

    potcar_mappings = PBE_GW_POTCAR_MAPPINGS

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    _incar_updates = dict(
        NGXF__density_a=20,
        NGYF__density_b=20,
        NGZF__density_c=20,
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
    )
