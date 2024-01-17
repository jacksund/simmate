# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.pbe import (
    Relaxation__Vasp__WarrenLabPbe,
)

PBE_STATIC_SETTINGS = dict(
    IBRION=-1,  # (optional) locks everything between ionic steps
    NSW=0,  # this is the main static energy setting
    #            LAECHG=True, # currently only set in population analysis
    LCHARG=True,
    LORBIT=11,
    LVHAR=True,
    LWAVE=True,
    ALGO="Normal",  # was "Fast" before
)
# These settings are saved here to make it easier to add them to other static
# energy workflows


class StaticEnergy__Vasp__WarrenLabPbe(Relaxation__Vasp__WarrenLabPbe):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    PBE.
    """

    _incar_updates = PBE_STATIC_SETTINGS
