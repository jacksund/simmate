# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.mit import MITRelaxation

# This class used pymatgen's MITMDSet as it basis for settings.


class MITDynamicsTask(MITRelaxation):
    """
    Runs a molecular dynamics simulation using MIT Project settings. The lattice
    will remain fixed during the run.

    By default, this will run from 300-1200 Kelvin over 10,000 steps of 2
    femtoseconds, but start/end temperatures as well as step size/number can
    be adjusted when initializing this class. Note, setting parameters in the
    init is atypical for Simmate tasks, but we allow it for MD run because it
    does not affect the interopability of results -- that is, results can
    be compared accross runs regardless of temp/time.

    Provide your structure as the desired supercell, as the setup of this
    calculation does not modify your input structure.
    """

    # The settings used for this calculation are based on the MITRelaxation, but
    # we are updating/adding new settings here.
    # !!! we hardcode temperatures and time steps here, but may take these as inputs
    # in the future
    incar_base = MITRelaxation.incar.copy()
    incar_base.update(
        dict(
            TEBEG="Defaults to 300 but can be set by the user",  # start temperature
            TEEND="Defaults to 1200 but can be set by the user",  # end temperature
            POTIM="Defaults to 2 but can be set by the user",  # time step (in fs)
            NSW="Defaults to 10,000 but can be set by the user",  # number of steps
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
            ISYM=0,  # turn off symmetry
            ISIF=0,  # only update atom sites; lattice is fixed
            IBRION=0,  # turns on molecular dynamics
            KBLOCK=100,
            SMASS=0,
            PREC="Low",
        )
    )
    # because we no longer use LDAU, we can also remove all relevent settings from
    # the incar for clarity.
    incar_base.pop("multiple_keywords__smart_ldau")
    # Likewise, we set ISMEAR=0 and EDIFF above, so we no longer need smart_ismear
    incar_base.pop("multiple_keywords__smart_ismear")
    incar_base.pop("EDIFF")

    # For now, I turn off all error handlers.
    # TODO
    error_handlers = []

    def __init__(
        self,
        temperature_start: int = 300,
        temperature_end: int = 1200,
        time_step: float = 2,
        nsteps: int = 10000,
        # To support other options from the Simmate S3Task and Prefect Task
        **kwargs,
    ):
        # make a copy of the incar_base dict because we update its values
        incar = self.incar_base.copy()
        incar["TEBEG"] = temperature_start
        incar["TEEND"] = temperature_end
        incar["POTIM"] = time_step
        incar["NSW"] = nsteps

        # now inherit from parent S3Task class
        super().__init__(**kwargs)

    @classmethod
    def get_config(cls):
        """
        Grabs the overall settings from the class. This is useful for printing out
        settings for users to inspect.
        """
        return {
            key: getattr(cls, key)
            for key in [
                "__module__",
                "pre_sanitize_structure",
                "confirm_convergence",
                "functional",
                "incar_base",  # This is the only line changed vs. the base VaspTask
                "potcar_mappings",
            ]
        }
