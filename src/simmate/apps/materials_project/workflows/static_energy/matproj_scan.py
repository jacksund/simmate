# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj_scan import (
    Relaxation__Vasp__MatprojScan,
)


class StaticEnergy__Vasp__MatprojScan(Relaxation__Vasp__MatprojScan):
    """
    This task is a reimplementation of pymatgen's
    [MPScanStaticSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPScanStaticSet).
    """

    _incar_updates = dict(
        ALGO="Fast",
        NSW=0,
        LREAL=False,
        LVHAR=True,
        ISMEAR=-5,
        #
        EDIFFG="__remove__",
        IBRION="__remove__",
        ISIF="__remove__",   
    )
