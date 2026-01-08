# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.pbe_metal import (
    Relaxation__Vasp__PbeMetalWarren,
)
from simmate.apps.warren_lab.workflows.static_energy.pbe import PBE_STATIC_SETTINGS


class StaticEnergy__Vasp__PbeMetalWarren(Relaxation__Vasp__PbeMetalWarren):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    Metal relaxations using the PBE functional.
    """

    _incar_updates = PBE_STATIC_SETTINGS
