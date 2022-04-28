# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.static_energy import MatProjStaticEnergy


class MatProjNMRElectricFieldGradiant(MatProjStaticEnergy):
    """
    This task is a reimplementation of pymatgen's
    [MPNMRSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPNonSCFSet)
    with mode="efg" (Electric Field Gradient).
    """

    incar = MatProjStaticEnergy.incar.copy()
    incar.update(
        dict(
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
    )
    incar.pop("EDIFF__per_atom")
