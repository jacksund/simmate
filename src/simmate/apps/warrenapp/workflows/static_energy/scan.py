# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.relaxation.scan import Relaxation__Warren__Scan
from simmate.apps.warrenapp.workflows.static_energy.hse import hse_static_settings


class StaticEnergy__Warren__Scan(Relaxation__Warren__Scan):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    SCAN functional relaxation.
    """

    incar = Relaxation__Warren__Scan.incar.copy()
    incar.update(hse_static_settings)
