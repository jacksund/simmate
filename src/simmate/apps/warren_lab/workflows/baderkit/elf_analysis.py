# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.baderkit.workflows.elf_analysis import (
    ElfAnalysis__Baderkit__SpinElfAnalysis,
)
from simmate.apps.warren_lab.workflows.static_energy.pre_bader_badelf import (
    StaticEnergy__Vasp__PrebadelfScanWarren,
)
from simmate.toolkit import Structure
from simmate.workflows.base_flow_types import Workflow


class ElfAnalysis__VaspBaderkit__SpinElfAnalysisWarren(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out an ELF analysis on the resulting charge density.
    Uses the Warren lab r2SCAN settings.
    """

    use_database = False  # nested workflows save to DB instead

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        subworkflow_kwargs: dict = {},
        **kwargs,
    ):
        static_dir = directory / StaticEnergy__Vasp__PrebadelfScanWarren.name_full
        result = StaticEnergy__Vasp__PrebadelfScanWarren.run(
            structure=structure,
            command=command,
            source=source,
            directory=static_dir,
            **subworkflow_kwargs,
        ).result()

        # And run the ELF analysis on the resulting ELFCAR/CHGCAR
        analysis_dir = directory / ElfAnalysis__Baderkit__SpinElfAnalysis.name_full
        ElfAnalysis__Baderkit__SpinElfAnalysis.run(
            directory=analysis_dir,
            previous_directory=static_dir,
            source=result,
            **subworkflow_kwargs,
        ).result()
