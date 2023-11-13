# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.relaxation.pbe_metal import Relaxation__Warren__PbeMetal
from simmate.apps.warrenapp.workflows.static_energy.pbe import pbe_static_settings


class StaticEnergy__Warren__PbeMetal(Relaxation__Warren__PbeMetal):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    Metal relaxations using the PBE functional.
    """

    incar = Relaxation__Warren__PbeMetal.incar.copy()
    incar.update(pbe_static_settings)
