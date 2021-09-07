# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
)


class Quality00RelaxationTask(VaspTask):

    # This uses the PBE functional with POTCARs that have lower electron counts
    # and convergence criteria when available.
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS_LOW_QUALITY

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
            "metal": dict(ISMEAR=1, SIGMA=0.1,),
            "non-metal": dict(ISMEAR=0, SIGMA=0.05,),
        },
    )
