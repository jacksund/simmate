# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.electronic_structure.base_density_of_states import (
    VaspDensityOfStates,
)
from simmate.calculators.vasp.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class ElectronicStructure__Vasp__MatprojDensityOfStates(
    VaspDensityOfStates, Relaxation__Vasp__Matproj
):
    """
    This task is a reimplementation of pymatgen's
    [MPNonSCFSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPNonSCFSet)
    with mode="uniform".

    Calculates the band structure using Materials Project HSE settings.
    """

    incar = Relaxation__Vasp__Matproj.incar.copy()
    incar.update(
        IBRION=-1,
        LCHARG=False,
        LORBIT=11,
        LWAVE=False,
        NSW=0,
        ISYM=2,
        ICHARG=11,
        ISMEAR=-5,
        NEDOS=2001,
    )
    incar.pop("MAGMOM__smart_magmom")
