# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation import MatprojRelaxation


class MatVirtualLabElastic(MatprojRelaxation):
    """
    This task is a reimplementation of pymatgen's
    [MVLElasticSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLElasticSet).
    """

    incar = MatprojRelaxation.incar.copy()
    incar.update(
        dict(
            IBRION=6,
            NFREE=2,
            POTIM=0.015,  # pymatgen uses this as a parameter
        )
    )
    # incar.pop("NPAR")  # pymatgen forcibly removes NPAR
