# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)


class Nmr__Vasp__MatprojChemicalShifts(StaticEnergy__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MPNMRSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPNonSCFSet)
    with mode="cs" (Chemical Shift).
    """

    incar = StaticEnergy__Vasp__Matproj.incar.copy()
    incar.update(
        dict(
            LCHIMAG=True,
            EDIFF=-1.0e-10,
            ISYM=0,
            LCHARG=False,
            LNMR_SYM_RED=True,
            NELMIN=10,
            NSLPLINE=True,
            PREC="ACCURATE",
            SIGMA=0.01,
        )
    )
    incar.pop("EDIFF__per_atom")
