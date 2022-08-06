# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation import MatprojHSERelaxation


class MatprojHSEStaticEnergy(MatprojHSERelaxation):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet)
    but converted to a static energy calculation. The pymatgen library doesn't
    not have an HSE static energy, so this is the make-shift alternative.
    """

    incar = MatprojHSERelaxation.incar.copy()
    incar.update(
        dict(
            IBRION=-1,  # (optional) locks everything between ionic steps
            NSW=0,  # this is the main static energy setting
            LAECHG=True,
            LCHARG=True,
            LORBIT=11,
            LVHAR=True,
            LWAVE=False,
            ALGO="Normal",  # was "Fast" before
        )
    )
