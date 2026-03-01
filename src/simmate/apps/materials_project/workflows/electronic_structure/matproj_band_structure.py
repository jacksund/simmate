# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)
from simmate.apps.vasp.workflows.electronic_structure.base_band_structure import (
    VaspBandStructure,
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

    parent_workflows = ["electronic-structure.vasp.matproj-full"]
    _incar_updates = dict(
        LCHARG=False,
        LORBIT=11,
        LWAVE=False,
        NSW=0,
        ISYM=0,
        ICHARG=11,
        ISMEAR=0,
        SIGMA=0.2,
        MAGMOM__smart_magmom="__remove__",
        IBRION="__remove__",
        ISIF="__remove__",
    )
