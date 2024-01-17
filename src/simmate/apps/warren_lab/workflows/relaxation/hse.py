# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.inputs.potcar_mappings import HSE_POTCAR_MAPPINGS
from simmate.apps.warren_lab.workflows.relaxation.pbe import (
    Relaxation__Vasp__WarrenLabPbe,
)


class Relaxation__Vasp__WarrenLabHse(Relaxation__Vasp__WarrenLabPbe):
    """
    Runs a VASP relaxation calculation using Warren Lab HSE settings.
    """

    description_doc_short = "Warren Lab presets for HSE geometry optimization"
    # some potcars don't work with HSE in VASP 5.x.x. I change them here
    # in the hopes that they will work properly.
    potcar_mappings = HSE_POTCAR_MAPPINGS

    _incar_updats = dict(
        ALGO="Damped",  # We use Damped because it is the recommended setting by
        # by VASP (https://www.vasp.at/wiki/index.php/LHFCALC)
        HFSCREEN=0.2,
        ICHARG=1,
        LHFCALC=True,
        PRECFOCK="Fast",
        TIME=0.2,  # This is lower than the recommended setting (0.5) when using the
        # Damped tag because calculations struggle to converge.
        # VASP also suggests lowering it if convergence isn't reached so there
        # is precedence for this.
        VDW_S8=2.310,  # these three tags are necessary for IVDW 12 with HSE06
        VDW_A1=0.383,
        VDW_A2=5.685,
    )
