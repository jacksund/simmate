# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.electronic_structure.base_band_structure import (
    VaspBandStructure,
)
from simmate.calculators.vasp.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class ElectronicStructure__Vasp__MatprojBandStructure(
    VaspBandStructure, Relaxation__Vasp__Matproj
):
    """
    This task is a reimplementation of pymatgen's
    [MPNonSCFSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPNonSCFSet)
    with mode="line".

    Calculates the band structure using Materials Project HSE settings.
    """

    incar = Relaxation__Vasp__Matproj.incar.copy()
    incar.update(
        IBRION=-1,
        LCHARG=False,
        LORBIT=11,
        LWAVE=False,
        NSW=0,
        ISYM=0,
        ICHARG=11,
        ISMEAR=0,
        SIGMA=0.01,
    )
    incar.pop("MAGMOM__smart_magmom")
