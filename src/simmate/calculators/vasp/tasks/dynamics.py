# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.mit import MITRelaxation

# This class used pymatgen's MITMDSet as it basis for settings.


class MITDynamicsTask(MITRelaxation):

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    # !!! we hardcode temperatures and time steps here, but may take these as inputs
    # in the future
    incar = MITRelaxation.incar.copy()
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
            NSIM=4,  # number of bands to run in parallel  # !!! Should this be moved to config?
            ISYM=0,  # turn off symmetry
            ISIF=0,  # only update atom sites
            IBRION=0,  # turns on molecular dynamics
            NBLOCK=1,
            KBLOCK=100,
            SMASS=0,
            POTIM=2,  # time step (in fs)
            PREC="Low",
        )
    )
    # because we no longer use LDAU, we can also remove all relevent settings from
    # the incar for clarity.
    incar.pop("multiple_keywords__smart_ldau")
    # Likewise, we set ISMEAR=0 and EDIFF above, so we no longer need smart_ismear
    incar.pop("multiple_keywords__smart_ismear")
    incar.pop("EDIFF")

    # For now, I turn off all error handlers.
    # TODO
    error_handlers = []
