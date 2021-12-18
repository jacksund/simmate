# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.base import VaspTask
from simmate.calculators.vasp.inputs.potcar_mappings import (
    PBE_ELEMENT_MAPPINGS_LOW_QUALITY,
)


class Quality02Relaxation(VaspTask):

    # returns structure separately from vasprun object
    return_final_structure = True

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
        EDIFF=1e-3,
        EDIFFG=1e-2,
        ENCUT=375,  # !!! Should this be based on the element type?
        ISIF=3,
        NSW=100,
        IBRION=2,  # for cases of bad starting sites
        POTIM=0.02,
        LCHARG=False,
        LWAVE=False,
        KSPACING=0.5,
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
