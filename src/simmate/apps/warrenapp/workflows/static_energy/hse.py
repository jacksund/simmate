# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.relaxation.hse import Relaxation__Warren__Hse

hse_static_settings = dict(
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


class StaticEnergy__Warren__Hse(Relaxation__Warren__Hse):
    """
    Performs a static energy calculation based on the settings for Warren Lab
    HSE functional relaxation.
    """

    incar = Relaxation__Warren__Hse.incar.copy()
    incar.update(hse_static_settings)
