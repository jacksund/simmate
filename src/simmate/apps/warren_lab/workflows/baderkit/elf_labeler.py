# -*- coding: utf-8 -*-


from simmate.apps.warren_lab.workflows.baderkit.base import BaderkitStagedBase
from simmate.apps.baderkit.workflows import Baderkit__Baderkit__ElfLabeler, Baderkit__Baderkit__SpinElfLabeler
from simmate.apps.warren_lab.workflows.static_energy.pre_bader_badelf import StaticEnergy__Vasp__PrebadelfPbesolWarren, StaticEnergy__Vasp__PrebadelfSpinPbesolWarren


class Baderkit__VaspBaderkit__ElfLabelerPbesolWarren(BaderkitStagedBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out ElfLabeler and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """
    
    workflows = [
        StaticEnergy__Vasp__PrebadelfPbesolWarren,
        Baderkit__Baderkit__ElfLabeler
        ]

class Baderkit__VaspBaderkit__SpinElfLabelerPbesolWarren(BaderkitStagedBase):
    """
    Runs a spin-polarized static energy calculation using an extra-fine FFT grid using vasp
    and then carries out ElfLabeler and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """
    
    workflows = [
        StaticEnergy__Vasp__PrebadelfSpinPbesolWarren,
        Baderkit__Baderkit__SpinElfLabeler
        ]
