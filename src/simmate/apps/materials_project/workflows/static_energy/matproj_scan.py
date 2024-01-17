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
        NSW=0,  # this is the main static energy setting
        LREAL=False,
        LORBIT=11,
        LVHAR=True,
        ISMEAR=-5,
    )
