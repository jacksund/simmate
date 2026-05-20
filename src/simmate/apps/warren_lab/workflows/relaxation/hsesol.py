# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.hse import Relaxation__Vasp__HseWarren, Relaxation__Vasp__SpinHseWarren


class Relaxation__Vasp__HsesolWarren(Relaxation__Vasp__HseWarren):
    """
    Runs a VASP relaxation calculation using Warren Lab HSEsol settings.
    """

    description_doc_short = "Warren Lab presets for HSEsol geometry optimization"

    _incar_updates = dict(
        IVDW=0,  # No d3 constants for HSEsol so we just turn of VDW corrections
        GGA="PS",  # Tells vasp to use PBEsol instead of PBE
    )

class Relaxation__Vasp__SpinHsesolWarren(Relaxation__Vasp__SpinHseWarren):
    """
    Runs a spin-polarized VASP relaxation calculation using Warren Lab HSEsol settings.
    """

    description_doc_short = "Warren Lab presets for HSEsol geometry optimization"

    _incar_updates = dict(
        IVDW=0,  # No d3 constants for HSEsol so we just turn of VDW corrections
        GGA="PS",  # Tells vasp to use PBEsol instead of PBE
    )
