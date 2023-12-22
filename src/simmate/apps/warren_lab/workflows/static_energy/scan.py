# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.scan import (
    Relaxation__Vasp__WarrenLabScan,
)
from simmate.apps.warren_lab.workflows.static_energy.hse import hse_static_settings


class StaticEnergy__Vasp__WarrenLabScan(Relaxation__Vasp__WarrenLabScan):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    SCAN functional relaxation.
    """

    incar = Relaxation__Vasp__WarrenLabScan.incar.copy()
    incar.update(hse_static_settings)
