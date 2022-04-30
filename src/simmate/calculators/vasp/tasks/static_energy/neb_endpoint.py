# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation import (
    MatVirtualLabCINEBEndpointRelaxation,
)


class NEBEndpointStaticEnergy(MatVirtualLabCINEBEndpointRelaxation):
    """
    Runs a VASP energy calculation using MIT Project settings, where some
    settings are adjusted to accomodate large supercells with defects.

    This is identical to relaxation/neb_endpoint, but just a single ionic step.

    You typically shouldn't use this workflow directly, but instead use the
    higher-level NEB workflows (e.g. diffusion/neb_all_paths or
    diffusion/neb_from_endpoints), which call this workflow for you.
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    incar = MatVirtualLabCINEBEndpointRelaxation.incar.copy()
    incar.update(
        dict(
            IBRION=-1,  # (optional) locks everything between ionic steps
            NSW=0,  # this is the main static energy setting
        )
    )
