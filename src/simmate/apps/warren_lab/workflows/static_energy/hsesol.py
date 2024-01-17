# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.hsesol import (
    Relaxation__Vasp__WarrenLabHsesol,
)
from simmate.apps.warren_lab.workflows.static_energy.hse import HSE_STATIC_SETTINGS


class StaticEnergy__Vasp__WarrenLabHsesol(Relaxation__Vasp__WarrenLabHsesol):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    HSEsol functional relaxation.
    """

    _incar_updates = HSE_STATIC_SETTINGS
