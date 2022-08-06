# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.relaxation.matproj_hse import (
    Relaxation__Vasp__MatprojHse,
)


class StaticEnergy__Vasp__MatprojHse(Relaxation__Vasp__MatprojHse):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet)
    but converted to a static energy calculation. The pymatgen library doesn't
    not have an HSE static energy, so this is the make-shift alternative.
    """

    incar = Relaxation__Vasp__MatprojHse.incar.copy()
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
