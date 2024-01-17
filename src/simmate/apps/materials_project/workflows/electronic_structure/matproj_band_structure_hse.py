# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj_hse import (
    Relaxation__Vasp__MatprojHse,
)
from simmate.apps.vasp.workflows.electronic_structure.base_band_structure import (
    VaspBandStructure,
)


class ElectronicStructure__Vasp__MatprojBandStructureHse(
    VaspBandStructure, Relaxation__Vasp__MatprojHse
):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet)
    with mode="line".

    Calculates the band structure using Materials Project HSE settings.
    """

    parent_workflows = ["electronic-structure.vasp.matproj-hse-full"]
    _incar_updates = dict(
        NSW=0,
        ISMEAR=0,
        SIGMA=0.05,
        ISYM=3,
        LCHARG=False,
        NELMIN=5,
    )
