# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.hsesol import (
    Relaxation__Vasp__HsesolWarren,
)
from simmate.apps.warren_lab.workflows.static_energy.hse import HSE_STATIC_SETTINGS


class StaticEnergy__Vasp__HsesolWarren(Relaxation__Vasp__HsesolWarren):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    HSEsol functional relaxation.
    """

    _incar_updates = HSE_STATIC_SETTINGS
