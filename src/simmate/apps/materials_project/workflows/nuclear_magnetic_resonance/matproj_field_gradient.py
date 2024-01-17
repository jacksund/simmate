# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)


class Nmr__Vasp__MatprojFieldGradient(StaticEnergy__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MPNMRSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPNMRSet)
    with mode="efg" (Electric Field Gradient).
    """

    _incar_updates = dict(
        ALGO="FAST",
        EDIFF=-1.0e-10,
        ISYM=0,
        LCHARG=False,
        LEFG=True,
        QUAD_EFG__smart_quad_efg=True,
        NELMIN=10,
        PREC="ACCURATE",
        SIGMA=0.01,
    )
