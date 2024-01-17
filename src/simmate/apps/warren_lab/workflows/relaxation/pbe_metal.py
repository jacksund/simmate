# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.pbe import (
    Relaxation__Vasp__WarrenLabPbe,
)


class Relaxation__Vasp__WarrenLabPbeMetal(Relaxation__Vasp__WarrenLabPbe):
    """
    Runs a VASP relaxation calculation using Warren Lab PBE functional settings
    with some adjusted settings to accomodate metals.
    """

    description_doc_short = "Warren Lab presets for metals"

    _incar_updates = dict(
        ISMEAR=1,
        SIGMA=0.2,
        KSPACING=0.3,
    )
