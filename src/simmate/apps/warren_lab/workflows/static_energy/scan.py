# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.scan import (
    Relaxation__Vasp__WarrenLabScan,
)
from simmate.apps.warren_lab.workflows.static_energy.hse import HSE_STATIC_SETTINGS


class StaticEnergy__Vasp__WarrenLabScan(Relaxation__Vasp__WarrenLabScan):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    SCAN functional relaxation.
    """

    _incar_updates = HSE_STATIC_SETTINGS
