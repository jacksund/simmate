# -*- coding: utf-8 -*-

from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS_LOW_QUALITY
from simmate.apps.vasp.workflows.base import VaspWorkflow


class Relaxation__Vasp__Quality01(VaspWorkflow):
    """
    Runs a VERY rough VASP geometry optimization.

    `Quality 01` indicates that on a scale from 00 to 04, these are ranked 01 in
    quality (with 04 being the highest quality).

    Typically, you'd only want to run this relaxation on structures that were
    randomly created (and thus likely very unreasonable). More precise relaxations
    should be done afterwards. Therefore, instead of using this calculation,
    we recommend only using the relaxation/staged workflow, which uses this
    calculation as a second step.
    """

    description_doc_short = "for randomly-created structures"

    # This uses the PBE functional with POTCARs that have lower electron counts
    # and convergence criteria when available.
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS_LOW_QUALITY

    # Make the unitcell relatively cubic before relaxing
    standardize_structure = "primitive-LLL"

    # These are all input settings for this task.
    _incar = dict(
        # These settings are the same for all structures regardless of composition.
        PREC="Normal",
        EDIFF=1e-3,
        EDIFFG=1e-2,
        ISIF=4,  # this fixes lattice volume
        NSW=75,
        IBRION=2,  # for cases of bad starting sites
        POTIM=0.2,
        LCHARG=False,
        LWAVE=False,
        KSPACING=0.6,
        # The type of smearing we use depends on if we have a metal, semiconductor,
        # or insulator. So we need to decide this using a keyword modifier.
        multiple_keywords__smart_ismear={
            "metal": dict(
                ISMEAR=1,
                SIGMA=0.08,
            ),
            "non-metal": dict(
                ISMEAR=0,
                SIGMA=0.05,
            ),
        },
    )
