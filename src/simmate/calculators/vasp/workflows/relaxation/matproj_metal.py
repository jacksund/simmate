# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class Relaxation__Vasp__MatprojMetal(Relaxation__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MPMetalRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPMetalRelaxSet).

    Runs a VASP relaxation calculation using MIT Project settings, where some
    settings are adjusted to accomodate metals. This include a denser kpt grid
    and proper smearing.
    """

    incar = Relaxation__Vasp__Matproj.incar.copy()
    incar.update(
        dict(
            ISMEAR=1,
            SIGMA=0.2,
            KSPACING=0.3,
        )
    )
