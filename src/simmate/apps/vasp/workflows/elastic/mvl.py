# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class Elastic__Vasp__Mvl(Relaxation__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MVLElasticSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLElasticSet).
    """

    incar = Relaxation__Vasp__Matproj.incar.copy()
    incar.update(
        dict(
            IBRION=6,
            NFREE=2,
            POTIM=0.015,  # pymatgen uses this as a parameter
        )
    )
    # incar.pop("NPAR")  # pymatgen forcibly removes NPAR
