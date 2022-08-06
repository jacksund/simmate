# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation import MatprojSCANRelaxation


class MatprojSCANStaticEnergy(MatprojSCANRelaxation):
    """
    This task is a reimplementation of pymatgen's
    [MPScanStaticSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPScanStaticSet).
    """

    incar = MatprojSCANRelaxation.incar.copy()
    incar.update(
        dict(
            NSW=0,  # this is the main static energy setting
            LREAL=False,
            LORBIT=11,
            LVHAR=True,
            ISMEAR=-5,
        )
    )
