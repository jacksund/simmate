# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.diffusion.neb_from_images_base import (
    VaspNebFromImagesWorkflow,
)
from simmate.calculators.vasp.workflows.relaxation.mit import Relaxation__Vasp__Mit


class Diffusion__Vasp__NebFromImagesMit(
    VaspNebFromImagesWorkflow, Relaxation__Vasp__Mit
):
    """
    This task is a reimplementation of pymatgen's
    [MITNEBSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITNEBSet).

    Runs a NEB relaxation on a list of structures (aka images) using MIT Project
    settings. The lattice remains fixed and symmetry is turned off for this
    relaxation.

    You shouldn't use this workflow directly, but instead use the higher-level
    NEB workflows (e.g. diffusion/neb_all_paths or diffusion/neb_from_endpoints),
    which call this workflow for you.
    """

    incar = Relaxation__Vasp__Mit.incar.copy()
    incar.update(
        dict(
            IBRION=1,
            ISYM=0,
            LCHARG=False,
            IMAGES__auto=True,
        )
    )
    incar.pop("multiple_keywords__smart_ldau")
