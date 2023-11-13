# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.relaxation.pbe import Relaxation__Warren__Pbe

pbe_static_settings = dict(
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


class StaticEnergy__Warren__Pbe(Relaxation__Warren__Pbe):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    PBE.
    """

    incar = Relaxation__Warren__Pbe.incar.copy()
    incar.update(pbe_static_settings)
