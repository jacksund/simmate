# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.hse import (
    Relaxation__Vasp__WarrenLabHse,
)


class Relaxation__Vasp__WarrenLabHsesol(Relaxation__Vasp__WarrenLabHse):
    """
    Runs a VASP relaxation calculation using Warren Lab HSEsol settings.
    """

    description_doc_short = "Warren Lab presets for HSEsol geometry optimization"

    _incar_updates = dict(
        IVDW=0,  # No d3 constants for HSEsol so we just turn of VDW corrections
        GGA="PS",  # Tells vasp to use PBEsol instead of PBE
    )
