# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.workflows.base_flow_types import Workflow
from simmate.toolkit import Structure

from simmate.apps.warren_lab.workflows.static_energy.pre_bader_badelf import StaticEnergy__Vasp__WarrenLabPrebadelfScan
from simmate.apps.baderkit.workflows.spin_elf_analysis import SpinElfAnalysisCalculation__Baderkit__SpinElfAnalysis


class ElfAnalysis__VaspBaderkit__ElfAnalysisWarrenlab(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out an ELF analysis on the resulting charge density.
    Uses the Warren lab r2SCAN settings.
    """
    
    use_database = False # nested workflows save to DB instead

    
    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        **kwargs,
    ):
        static_dir = directory / StaticEnergy__Vasp__WarrenLabPrebadelfScan.name_full
        result = StaticEnergy__Vasp__WarrenLabPrebadelfScan.run(
            structure=structure,
            command=command,
            source=source,
            directory=static_dir,
        ).result()

        # And run the ELF analysis on the resulting ELFCAR/CHGCAR
        analysis_dir = directory / SpinElfAnalysisCalculation__Baderkit__SpinElfAnalysis.name_full
        SpinElfAnalysisCalculation__Baderkit__SpinElfAnalysis.run(
            directory=analysis_dir,
            previous_directory=static_dir,
            source=result,
        ).result()
