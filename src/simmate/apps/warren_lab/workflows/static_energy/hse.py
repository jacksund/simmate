# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.hse import (
    Relaxation__Vasp__WarrenLabHse,
)

HSE_STATIC_SETTINGS = dict(
    IBRION=-1,  # (optional) locks everything between ionic steps
    NSW=0,  # this is the main static energy setting
    #            LAECHG=True, # currently only set in population analysis
    LCHARG=True,
    LORBIT=11,
    LVHAR=True,
    LWAVE=True,
    # The only difference between this and PBE is that we don't want to change
    # the ALGO tag to "Normal" for HSE. It's recommended to use ALGO="All" for
    # insulators or ALGO="Damped" for small bandgap/metals
)


class StaticEnergy__Vasp__WarrenLabHse(Relaxation__Vasp__WarrenLabHse):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    HSE functional relaxation.
    """

    _incar_updates = HSE_STATIC_SETTINGS
