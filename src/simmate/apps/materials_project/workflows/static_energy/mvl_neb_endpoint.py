# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.relaxation.mvl_neb_endpoint import (
    Relaxation__Vasp__MvlNebEndpoint,
)


class StaticEnergy__Vasp__MvlNebEndpoint(Relaxation__Vasp__MvlNebEndpoint):
    """
    Runs a VASP energy calculation using MIT Project settings, where some
    settings are adjusted to accomodate large supercells with defects.

    This is identical to relaxation/neb_endpoint, but just a single ionic step.

    You typically shouldn't use this workflow directly, but instead use the
    higher-level NEB workflows (e.g. diffusion/neb_all_paths or
    diffusion/neb_from_endpoints), which call this workflow for you.
    """

    _incar_updates = dict(
        IBRION=-1,  # (optional) locks everything between ionic steps
        NSW=0,
    )
