# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.mit import (
    Relaxation__Vasp__Mit,
)


class StaticEnergy__Vasp__Mit(Relaxation__Vasp__Mit):
    """
    Runs a VASP static energy calculation using MIT Project settings.

    This is identical to relaxation/mit, but just a single ionic step.
    """

    _incar_updates = dict(
        ALGO="Normal",
        IBRION=-1,  # (optional) locks everything between ionic steps
        NSW=0,
        KSPACING=0.4,  # was 0.5 # !!! This is where we are different from pymatgen
    )
