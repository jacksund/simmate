# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class Relaxation__Vasp__MvlGrainboundary(Relaxation__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MVLGBSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLGBSet).
    """

    description_doc_short = "based on pymatgen's MVLGBSet"

    _incar_updates = dict(
        LCHARG=False,
        NELM=60,
        PREC="Normal",
        EDIFFG=-0.02,
        ICHARG=0,
        NSW=200,
        EDIFF=0.0001,
        # pymatgen has user set is_metal, where default is True and there
        # is no advanced logic. We just assume metal for now.
        ISMEAR=1,
        LDAU=False,
        KSPACING=0.35,  # !!! this is approximate to pymatgen
        multiple_keywords__smart_ldau="__remove__",
    )
