# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj_hse import (
    Relaxation__Vasp__MatprojHse,
)


class Relaxation__Vasp__MatprojHsesol(Relaxation__Vasp__MatprojHse):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet).

    Runs a VASP relaxation calculation using Materials Project HSE settings with
    an additional HSEsol setting.
    """

    description_doc_short = "based on pymatgen's MPHSERelaxSet"

    # Tell VASP to use PBEsol instead of base PBE
    _incar_updates = dict(GGA="PS")
