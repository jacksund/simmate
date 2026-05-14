# -*- coding: utf-8 -*-


from simmate.apps.warren_lab.workflows.baderkit.base import BaderkitStagedBase
from simmate.apps.baderkit.workflows import Baderkit__Baderkit__Badelf, Baderkit__Baderkit__SpinBadelf
from simmate.apps.warren_lab.workflows.static_energy.pre_bader_badelf import StaticEnergy__Vasp__PrebadelfHseWarren, StaticEnergy__Vasp__PrebadelfSpinHseWarren


class Baderkit__VaspBaderkit__BadelfHseWarren(BaderkitStagedBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Hse settings.
    """
    
    workflows = [
        StaticEnergy__Vasp__PrebadelfHseWarren,
        Baderkit__Baderkit__Badelf
        ]

class Baderkit__VaspBaderkit__SpinBadelfHseWarren(BaderkitStagedBase):
    """
    Runs a spin-polarized static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Hse settings.
    """
    
    workflows = [
        StaticEnergy__Vasp__PrebadelfSpinHseWarren,
        Baderkit__Baderkit__SpinBadelf
        ]
