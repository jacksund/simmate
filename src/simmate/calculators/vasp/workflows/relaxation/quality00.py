# -*- coding: utf-8 -*-

from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
)
from simmate.calculators.vasp.workflows.base import VaspWorkflow


class Relaxation__Vasp__Quality00(VaspWorkflow):
    """
    Runs a very rough VASP geometry optimization with fixed lattice volume.
    `Quality 00` indicates these are absolute lowest quality settings used in
    our available presets.

    Typically, you'd only want to run this relaxation on structures that were
    randomly created (and thus likely very unreasonable). More precise relaxations
    should be done afterwards. Therefore, instead of using this calculation,
    we recommend only using the relaxation/staged workflow, which uses this
    calculation as a first step.
    """

    description_doc_short = "bare-bones settings for randomly-created structures"

    # This uses the PBE functional with POTCARs that have lower electron counts
    # and convergence criteria when available.
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS_LOW_QUALITY

    # Make the unitcell relatively cubic before relaxing
    standardize_structure = "primitive-LLL"

    # These are all input settings for this task.
    incar = dict(
        # These settings are the same for all structures regardless of composition.
        PREC="Low",
        EDIFF=2e-3,
        EDIFFG=-2e-1,
        ISIF=4,  # this fixes lattice volume
        NSW=75,
        IBRION=2,  # for cases of bad starting sites
        POTIM=0.02,
        LCHARG=False,
        LWAVE=False,
        KSPACING=0.75,
        # The type of smearing we use depends on if we have a metal, semiconductor,
        # or insulator. So we need to decide this using a keyword modifier.
        multiple_keywords__smart_ismear={
            "metal": dict(
                ISMEAR=1,
                SIGMA=0.1,
            ),
            "non-metal": dict(
                ISMEAR=0,
                SIGMA=0.05,
            ),
        },
    )
