# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.relaxation.hse import Relaxation__Warren__Hse


class Relaxation__Warren__Hsesol(Relaxation__Warren__Hse):
    """
    Runs a VASP relaxation calculation using Warren Lab HSEsol settings.
    """

    description_doc_short = "Warren Lab presets for HSEsol geometry optimization"

    incar = Relaxation__Warren__Hse.incar.copy()
    incar.update(
        IVDW=0,  # No d3 constants for HSEsol so we just turn of VDW corrections
        GGA="PS",  # Tells vasp to use PBEsol instead of PBE
    )
