# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.pbesol import (
    Relaxation__Vasp__WarrenLabPbesol,
)
from simmate.apps.warren_lab.workflows.static_energy.pbe import PBE_STATIC_SETTINGS


class StaticEnergy__Vasp__WarrenLabPbesol(Relaxation__Vasp__WarrenLabPbesol):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    PBEsol functional relaxation. This functional is generally considered to
    be more accurate for solids.
    (Phys. Rev. Lett. 102, 039902 (2009))
    """

    _incar_updates = PBE_STATIC_SETTINGS
