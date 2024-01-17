# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj import (
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

    description_doc_short = "based on pymatgen's MPMetalRelaxSet"

    _incar_updates = dict(
        ISMEAR=1,
        SIGMA=0.2,
        KSPACING=0.3,
    )
