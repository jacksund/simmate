# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.mvl_grainboundary import (
    Relaxation__Vasp__MvlGrainboundary,
)


class Relaxation__Vasp__MvlSlab(Relaxation__Vasp__MvlGrainboundary):
    """
    This task is a reimplementation of pymatgen's
    [MVLGBSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLGBSet)
    with slab_mode=True.
    """

    description_doc_short = "based on pymatgen's MVLGBSet(slab=True)"

    _incar_updates = dict(
        ISIF=2,
        NELMIN=8,
    )
