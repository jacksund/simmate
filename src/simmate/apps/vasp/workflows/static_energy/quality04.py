# -*- coding: utf-8 -*-

from simmate.apps.vasp.workflows.relaxation.quality04 import Relaxation__Vasp__Quality04


class StaticEnergy__Vasp__Quality04(Relaxation__Vasp__Quality04):
    """
    Runs a rough VASP static energy calculation.

    `Quality 04` relates to our ranking of relaxation qualities, where this
    calculation uses the same settings as the Quality04Relaxation.

    Note, even though this is currently our highest quality preset, these
    settings are still only suitable for high-throughput calculations or massive
    supercells. Settings are still below MIT and Materials Project quality.

    Most commonly, this is used in evolutionary searches (for structure
    prediction). We recommend instead using the relaxation/staged workflow,
    which uses this calculation as the sixth and final step -- after a series
    of rough relaxations are done.
    """

    _incar_updates = dict(
        ALGO="Normal",
        IBRION=-1,  # (optional) locks everything between ionic steps
        NSW=0,  # this is the main static energy setting
        ISMEAR=-5,  # was 0 for non-metals and 1 for metals
        SIGMA=0.05,  # was 0.05 for non-metals and 0.06 for metals
        multiple_keywords__smart_ismear="__remove__",
    )
