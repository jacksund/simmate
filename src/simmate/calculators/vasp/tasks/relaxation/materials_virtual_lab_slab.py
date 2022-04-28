# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation import (
    MatVirtualLabGrainBoundaryRelaxation as MVLGBRelax,
)


class MatVirtualLabSlabRelaxation(MVLGBRelax):
    """
    This task is a reimplementation of pymatgen's
    [MVLGBSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLGBSet)
    with slab_mode=True.
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    incar = MVLGBRelax.incar.copy()
    incar.update(
        dict(
            ISIF=2,
            NELMIN=8,
        )
    )
