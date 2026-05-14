# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.baderkit.base import BaderkitStagedBase
from simmate.apps.baderkit.workflows import Baderkit__Baderkit__Bader
from simmate.apps.warren_lab.workflows.static_energy.pre_bader_badelf import StaticEnergy__Vasp__PrebaderWarren


class Baderkit__VaspBaderkit__BaderWarren(BaderkitStagedBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density.
    """
    
    workflows = [
        StaticEnergy__Vasp__PrebaderWarren,
        Baderkit__Baderkit__Bader
        ]
