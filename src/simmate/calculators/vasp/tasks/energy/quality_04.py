# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.quality_04 import Quality04Relaxation


class Quality04Energy(Quality04Relaxation):
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

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    # !!! we hardcode temperatures and time steps here, but may take these as inputs
    # in the future
    incar = Quality04Relaxation.incar.copy()
    incar.update(
        dict(
            ALGO="Normal",
            IBRION=-1,  # (optional) locks everything between ionic steps
            NSW=0,  # this is the main static energy setting
            ISMEAR=-5,  # was 0 for non-metals and 1 for metals
            SIGMA=0.05,  # was 0.05 for non-metals and 0.06 for metals
        )
    )
    # We set ISMEAR=0 and SIGMA above, so we no longer need smart_ismear
    incar.pop("multiple_keywords__smart_ismear")
