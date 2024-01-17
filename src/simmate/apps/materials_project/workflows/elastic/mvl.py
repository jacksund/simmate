# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class Elastic__Vasp__Mvl(Relaxation__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MVLElasticSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLElasticSet).
    """

    _incar_updates = dict(
        IBRION=6,
        NFREE=2,
        POTIM=0.015,  # pymatgen uses this as a parameter
        NPAR="__remove__",  # pymatgen forcibly removes NPAR
    )
