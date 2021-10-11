# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.third_party.mit import MITRelaxationTask

from simmate.calculators.vasp.error_handlers.all import (
    TetrahedronMesh,
    Eddrmm,
    NonConvergingErrorHandler,
)

class MITDynamicsTask(MITRelaxationTask):

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    # !!! we hardcode temperatures and time steps here, but may take these as inputs
    # in the future
    incar = MITRelaxationTask.incar.copy()
    incar.update(
        dict(
            TEBEG=300,  # start temperature
            TEEND=1200,  # end temperature
            NSW=10000,  # number of steps
            EDIFF__per_atom=1e-06,
            LSCALU=False,
            LCHARG=False,
            LPLANE=False,
            LWAVE=True,
            ISMEAR=0,
            NELMIN=4,
            LREAL=True,
            BMIX=1,
            MAXMIX=20,
            NELM=500,
            NSIM=4,
            ISYM=0,
            ISIF=0,
            IBRION=0,
            NBLOCK=1,
            KBLOCK=100,
            SMASS=0,
            POTIM=2,  # time step
            PREC="Low",
            # ISPIN=2,  # same as before
            LDAU=False,
        )
    )
    # because we no longer use LDAU, we can also remove all relevent settings from
    # the incar for clarity.
    incar.pop("multiple_keywords__smart_ldau")
    # Likewise, we set ISMEAR=0 and EDIFF above, so we no longer need smart_ismear
    incar.pop("multiple_keywords__smart_ismear")
    incar.pop("EDIFF")

    # We reduce the number of error handlers used on dynamics because many
    # error handlers are based on finding the global minimum & converging, which
    # not what we're doing with dynmaics
    error_handlers = [
        TetrahedronMesh(),
        Eddrmm(),
        NonConvergingErrorHandler(),
    ]
