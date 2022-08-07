# -*- coding: utf-8 -*-

from simmate.calculators.vasp.workflows.dynamics.base import DynamicsWorkflow
from simmate.calculators.vasp.workflows.relaxation.matproj import (
    Relaxation__Vasp__Matproj,
)


class Dynamics__Vasp__Matproj(DynamicsWorkflow, Relaxation__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MPMDSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPMDSet).

    Runs a molecular dynamics simulation using MIT Project settings. The lattice
    will remain fixed during the run.

    By default, this will run from 300-1200 Kelvin over 10,000 steps of 2
    femtoseconds, but start/end temperatures as well as step number can
    be adjusted when initializing this class. Note, setting parameters in the
    init is atypical for Simmate tasks, but we allow it for MD run because it
    does not affect the interopability of results -- that is, results can
    be compared accross runs regardless of temp/time.

    Provide your structure as the desired supercell, as the setup of this
    calculation does not modify your input structure.
    """

    confirm_convergence = False

    incar = Relaxation__Vasp__Matproj.incar.copy()
    incar.update(
        dict(
            # Unique to this task, we want to allow users to set these temperatures
            # but to keep with Simmate's strategy of showing all settings up-front,
            # we set these messages here.
            # TODO: consider making a "__user_input" incar tag that accepts a default
            TEBEG="Defaults to 300 but can be set by the user",  # start temperature
            TEEND="Defaults to 1200 but can be set by the user",  # end temperature
            # !!! pymatgen modifies POTIM for H-containing structures
            POTIM="Defaults to 2 but can be set by the user",
            NSW="Defaults to 10,000 but can be set by the user",  # number of steps
            #
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
            NSIM=4,  # same as VASP default but pymatgen sets this
            ISYM=0,  # turn off symmetry
            ISIF=0,  # only update atom sites; lattice is fixed; no lattice stress
            IBRION=0,  # turns on molecular dynamics
            KBLOCK=100,
            SMASS=0,
            ISPIN=1,  # pymatgen makes this a kwarg but we fix it to pmg's default
            PREC="Normal",
            NBLOCK=1,  # same as VASP default but pymatgen sets this
            ADDGRID=True,
        )
    )
    incar.pop("MAGMOM__smart_magmom")
    incar.pop("multiple_keywords__smart_ldau")
    incar.pop("ENCUT")

    # For now, I turn off all error handlers.
    # TODO
    error_handlers = []
