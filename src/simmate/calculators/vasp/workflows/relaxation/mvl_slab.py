# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.relaxation.mvl_grainboundary import (
    Relaxation__Vasp__MvlGrainboundary,
)


class Relaxation__Vasp__MvlSlab(Relaxation__Vasp__MvlGrainboundary):
    """
    This task is a reimplementation of pymatgen's
    [MVLGBSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLGBSet)
    with slab_mode=True.
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    incar = Relaxation__Vasp__MvlGrainboundary.incar.copy()
    incar.update(
        dict(
            ISIF=2,
            NELMIN=8,
        )
    )
