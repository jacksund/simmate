# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.static_energy import MatprojStaticEnergy


class MatprojNMRChemicalShifts(MatprojStaticEnergy):
    """
    This task is a reimplementation of pymatgen's
    [MPNMRSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPNonSCFSet)
    with mode="cs" (Chemical Shift).
    """

    incar = MatprojStaticEnergy.incar.copy()
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
