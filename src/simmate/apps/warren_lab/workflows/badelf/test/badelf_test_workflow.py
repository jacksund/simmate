# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.static_energy.pbesol import (
    StaticEnergy__Vasp__WarrenLabPbesol,
)
from simmate.engine import StagedWorkflow


class StaticEnergy__Vasp__WarrenLabPrebadelfTest(StaticEnergy__Vasp__WarrenLabPbesol):
    """
    Runs a static energy calculation with low settings for testing the badelf
    algorithm
    """

    error_handlers = []
    _incar_updates = dict(
        NGX=35,
        NGY=35,
        NGZ=35,
        LWAVE=False,
        LELF=True,  # Writes the ELFCAR
        NPAR=1,  # Must be set if LELF is set
        PREC="Single",  # ensures CHGCAR grid matches ELFCAR grid
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
        KSPACING=0.5,  # decreasing kpoint sampling for faster calculation
        ENCUT=300,  # decreasing energy cutoff for faster calculation
    )


class StagedCalculation__Badelf__BadelfTest(StagedWorkflow):
    """
    Runs a static energy calculation using very low settings followed by a
    badelf run. This is intended for testing only and is not recommended for
    general use.
    """
    subworkflow_names = [
        "static-energy.vasp.warren-lab-prebadelf-test",
        "bad-elf.badelf.badelf",
        ]
    
    one_folder = True
