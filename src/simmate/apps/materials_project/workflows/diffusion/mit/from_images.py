# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.mit import (
    Relaxation__Vasp__Mit,
)
from simmate.apps.vasp.error_handlers import Frozen, Unconverged, Walltime
from simmate.apps.vasp.workflows.diffusion import VaspNebFromImagesWorkflow


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

    _incar_updates = dict(
        IBRION=1,
        ISYM=0,
        LCHARG=False,
        IMAGES__auto=True,
    )

    # Because of NEB's unique folder structure, many error handlers are broken
    # and cannot be used. We go through the list that is broken and remove them
    error_handlers = [
        handler
        for handler in Relaxation__Vasp__Mit.error_handlers
        if type(handler) not in [Walltime, Unconverged, Frozen]
    ]
