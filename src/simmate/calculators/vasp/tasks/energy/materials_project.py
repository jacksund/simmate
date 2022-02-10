# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.materials_project import (
    MatProjRelaxation,
)

from simmate.calculators.vasp.error_handlers import (
    TetrahedronMesh,
    Eddrmm,
    NonConvergingErrorHandler,
)


class MatProjStaticEnergy(MatProjRelaxation):
    """
    Runs a VASP static energy calculation using Materials Project settings.

    This is identical to relaxation/matproj, but just a single ionic step.
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    # !!! we hardcode temperatures and time steps here, but may take these as inputs
    # in the future
    incar = MatProjRelaxation.incar.copy()
    incar.update(
        dict(
            IBRION=-1,  # (optional) locks everything between ionic steps
            NSW=0,  # this is the main static energy setting
        )
    )

    # We reduce the number of error handlers used on static because many
    # error handlers are based on finding the global minimum & converging, which
    # not what we're doing with static
    error_handlers = [
        TetrahedronMesh(),
        Eddrmm(),
        NonConvergingErrorHandler(),
    ]
