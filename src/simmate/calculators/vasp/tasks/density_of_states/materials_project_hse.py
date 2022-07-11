# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.density_of_states import VaspDensityOfStates
from simmate.calculators.vasp.tasks.relaxation import MatprojHSERelaxation


class MatprojHSEDensityOfStates(VaspDensityOfStates, MatprojHSERelaxation):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet)
    with mode="uniform".

    Calculates the band structure using Materials Project HSE settings.
    """

    incar = MatprojHSERelaxation.incar.copy()
    incar.update(
        NSW=0,
        ISMEAR=0,
        SIGMA=0.05,
        ISYM=3,
        LCHARG=False,
        NELMIN=5,
    )
