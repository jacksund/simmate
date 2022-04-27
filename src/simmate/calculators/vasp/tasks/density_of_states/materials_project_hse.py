# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.density_of_states import VaspDensityOfStates
from simmate.calculators.vasp.tasks.relaxation import MatProjHSERelaxation


class MatProjHSEDensityOfStates(VaspDensityOfStates, MatProjHSERelaxation):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet)
    with mode="uniform".

    Calculates the band structure using Materials Project HSE settings.
    """

    incar = MatProjHSERelaxation.incar.copy()
    incar.update(
        NSW=0,
        ISMEAR=0,
        SIGMA=0.05,
        ISYM=3,
        LCHARG=False,
        NELMIN=5,
    )
