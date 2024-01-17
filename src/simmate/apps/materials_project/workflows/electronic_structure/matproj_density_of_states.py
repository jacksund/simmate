# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)
from simmate.apps.vasp.workflows.electronic_structure import VaspDensityOfStates


class ElectronicStructure__Vasp__MatprojDensityOfStates(
    VaspDensityOfStates, Relaxation__Vasp__Matproj
):
    """
    This task is a reimplementation of pymatgen's
    [MPNonSCFSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPNonSCFSet)
    with mode="uniform".

    Calculates the band structure using Materials Project HSE settings.
    """

    parent_workflows = ["electronic-structure.vasp.matproj-full"]
    _incar_updates = dict(
        IBRION=-1,
        LCHARG=False,
        LORBIT=11,
        LWAVE=False,
        NSW=0,
        ISYM=2,
        ICHARG=11,
        ISMEAR=-5,
        NEDOS=2001,
        MAGMOM__smart_magmom="__remove__",
    )
