# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.mit import MITRelaxation

from simmate.calculators.vasp.error_handlers import (
    TetrahedronMesh,
    Eddrmm,
    NonConverging,
)


class MITStaticEnergy(MITRelaxation):
    """
    Runs a VASP static energy calculation using MIT Project settings.

    This is identical to relaxation/mit, but just a single ionic step.
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    incar = MITRelaxation.incar.copy()
    incar.update(
        dict(
            ALGO="Normal",
            IBRION=-1,  # (optional) locks everything between ionic steps
            NSW=0,  # this is the main static energy setting
            KSPACING=0.4,  # was 0.5 # !!! This is where we are different from pymatgen right now
        )
    )
