# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class StaticEnergy__Vasp__Matproj(Relaxation__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MPStaticSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPStaticSet).

    Runs a VASP static energy calculation using Materials Project settings.

    This is identical to relaxation/Matproj, but just a single ionic step.
    """

    incar = Relaxation__Vasp__Matproj.incar.copy()
    incar.update(
        dict(
            IBRION=-1,  # (optional) locks everything between ionic steps
            NSW=0,  # this is the main static energy setting
            LAECHG=True,
            LCHARG=True,
            LORBIT=11,
            LVHAR=True,
            LWAVE=False,
            ALGO="Normal",  # was "Fast" before
        )
    )
