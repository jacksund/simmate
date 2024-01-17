# -*- coding: utf-8 -*-

from simmate.apps.badelf.workflows.badelf import BadElf__Badelf__Badelf
from simmate.apps.badelf.workflows.base import VaspBadElfBase
from simmate.apps.warren_lab.workflows.static_energy.pbesol import (
    StaticEnergy__Vasp__WarrenLabPbesol,
)


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


class BadElf__Badelf__BadelfTest(VaspBadElfBase):
    """
    Runs a static energy calculation using very low settings followed by a
    badelf run. This is intended for testing only and is not recommended for
    general use.
    """

    static_energy_workflow = StaticEnergy__Vasp__WarrenLabPrebadelfTest
    badelf_workflow = BadElf__Badelf__Badelf
