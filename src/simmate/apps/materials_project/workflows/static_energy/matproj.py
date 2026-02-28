# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class StaticEnergy__Vasp__Matproj(Relaxation__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MPStaticSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPStaticSet).

    Runs a VASP static energy calculation using Materials Project settings.

    This is identical to relaxation/Matproj, but just a single ionic step.
    """

    _incar_updates = dict(
        NSW=0,
        LCHARG=True,
        LREAL=False,
        #
        IBRION="__remove__",
        ISIF="__remove__",
    )
