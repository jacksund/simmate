# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
)


class Quality04Relaxation(VaspTask):
    """
    Runs a rough VASP geometry optimization.

    `Quality 04` indicates that on a scale from 00 to 04, these are ranked 04 in
    quality (with 04 being the highest quality).

    Note, even though this is currently our highest quality preset, these
    settings are still only suitable for high-throughput calculations or massive
    supercells. Settings are still below MIT and Materials Project quality.

    Typically, you'd only want to run this relaxation on structures that were
    randomly created (and thus likely very unreasonable). Therefore, instead of
    using this calculation, we recommend only using the relaxation/staged
    workflow, which uses this calculation as a fifth step (and final relaxation).
    """

    # This uses the PBE functional with POTCARs that have lower electron counts
    # and convergence criteria when available.
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS_LOW_QUALITY

    # because this calculation is such a low quality we don't raise an error
    # if the calculation fails to converge
    confirm_convergence = False

    # Make the unitcell relatively cubic before relaxing
    pre_sanitize_structure = True

    # These are all input settings for this task.
    incar = dict(
        # These settings are the same for all structures regardless of composition.
        PREC="Normal",
        EDIFF=1e-5,
        ENCUT=450,  # !!! Should this be based on the element type?
        ISIF=3,
        NSW=100,
        IBRION=1,
        POTIM=0.02,
        LCHARG=False,
        LWAVE=False,
        KSPACING=0.4,
        # The type of smearing we use depends on if we have a metal, semiconductor,
        # or insulator. So we need to decide this using a keyword modifier.
        multiple_keywords__smart_ismear={
            "metal": dict(
                ISMEAR=1,
                SIGMA=0.06,
            ),
            "non-metal": dict(
                ISMEAR=0,
                SIGMA=0.05,
            ),
        },
    )
