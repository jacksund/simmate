# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.pbe import (
    Relaxation__Vasp__WarrenLabPbe,
)


class Relaxation__Vasp__WarrenLabPbesol(Relaxation__Vasp__WarrenLabPbe):
    """
    Runs a VASP relaxation calculation using Warren Lab HSE settings.
    """

    description_doc_short = "Warren Lab presets for HSE geometry optimization"

    incar = Relaxation__Vasp__WarrenLabPbe.incar.copy()
    incar.update(GGA="PS")  # Tells vasp to use PBEsol instead of PBE
