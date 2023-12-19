# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.relaxation.pbe import Relaxation__Warren__Pbe


class Relaxation__Warren__Pbesol(Relaxation__Warren__Pbe):
    """
    Runs a VASP relaxation calculation using Warren Lab HSE settings.
    """

    description_doc_short = "Warren Lab presets for HSE geometry optimization"

    incar = Relaxation__Warren__Pbe.incar.copy()
    incar.update(GGA="PS")  # Tells vasp to use PBEsol instead of PBE
