# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.pbe_metal import (
    Relaxation__Vasp__WarrenLabPbeMetal,
)
from simmate.apps.warren_lab.workflows.static_energy.pbe import pbe_static_settings


class StaticEnergy__Vasp__WarrenLabPbeMetal(Relaxation__Vasp__WarrenLabPbeMetal):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    Metal relaxations using the PBE functional.
    """

    incar = Relaxation__Vasp__WarrenLabPbeMetal.incar.copy()
    incar.update(pbe_static_settings)
