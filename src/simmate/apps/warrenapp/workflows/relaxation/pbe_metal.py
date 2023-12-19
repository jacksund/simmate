# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.relaxation.pbe import Relaxation__Warren__Pbe


class Relaxation__Warren__PbeMetal(Relaxation__Warren__Pbe):
    """
    Runs a VASP relaxation calculation using Warren Lab PBE functional settings
    with some adjusted settings to accomodate metals.
    """

    description_doc_short = "Warren Lab presets for metals"

    incar = Relaxation__Warren__Pbe.incar.copy()
    incar.update(
        ISMEAR=1,
        SIGMA=0.2,
        KSPACING=0.3,
    )
