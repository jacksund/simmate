# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.workflows.base_flow_types import Workflow
from simmate.toolkit import Structure

from simmate.apps.warren_lab.workflows.static_energy.pbesol import StaticEnergy__Vasp__WarrenLabPbesol
from simmate.apps.baderkit.workflows.spin_elf_analysis import SpinElfAnalysisCalculation__Baderkit__SpinElfAnalysis
from simmate.apps.baderkit.workflows.bader import BaderkitChargeAnalysis__Baderkit__Bader


class ElfAnalysis__VaspBaderkit__ElfRadiiWarrenlab(Workflow):
    """
    An ElfAnalysis workflow with the goal of calculating the radii in
    each atom-neighbor pair of the system as well as additional charge
    data. This has potential use in an ML model for ionic radii.
    
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out a Bader charge analysis and ELF analysis.
    """
    
    use_database = False

    
    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        **kwargs,
    ):
        # First we run a static energy calculation
        static_dir = directory / StaticEnergy__Vasp__WarrenLabPreRadii.name_full
        result = StaticEnergy__Vasp__WarrenLabPreRadii.run(
            structure=structure,
            command=command,
            source=source,
            directory=static_dir,
        ).result()
        
        # Next we run a Bader analysis
        bader_dir = directory / BaderkitChargeAnalysis__Baderkit__Bader.name_full
        BaderkitChargeAnalysis__Baderkit__Bader.run(
            directory=bader_dir,
            previous_directory=static_dir,
            source=result,
            )

        # And run the ELF analysis
        analysis_dir = directory / SpinElfAnalysisCalculation__Baderkit__SpinElfAnalysis.name_full
        SpinElfAnalysisCalculation__Baderkit__SpinElfAnalysis.run(
            directory=analysis_dir,
            previous_directory=static_dir,
            source=result,
        ).result()


class StaticEnergy__Vasp__WarrenLabPreRadii(StaticEnergy__Vasp__WarrenLabPbesol):
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
        NGX__density_a=11, # set grid and fine grid to same, reasonably accurate value
        NGY__density_b=11,
        NGZ__density_c=11,
        NGXF__density_a=11,
        NGYF__density_b=11,
        NGZF__density_c=11,
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
        LELF=True, # write ELFCAR
        NPAR=1, # must be set for ELF calc
    )
