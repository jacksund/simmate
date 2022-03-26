# -*- coding: utf-8 -*-

import os

from simmate.toolkit import Structure
from simmate.calculators.vasp.inputs import Incar, Poscar, Kpoints, Potcar
from simmate.calculators.vasp.tasks.relaxation.mit import MITRelaxation

# This class used pymatgen's MITMDSet as it basis for settings.

# TODO: add MVLNPTMDSet and MPMDSet


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
    incar = MITRelaxation.incar.copy()
    incar.update(
        dict(
            # Unique to this task, we want to allow users to set these temperatures
            # but to keep with Simmate's strategy of showing all settings up-front,
            # we set these messages here.
            TEBEG="Defaults to 300 but can be set by the user",  # start temperature
            TEEND="Defaults to 1200 but can be set by the user",  # end temperature
            POTIM="Defaults to 2 but can be set by the user",  # time step (in fs)
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
            ISYM=0,  # turn off symmetry
            ISIF=0,  # only update atom sites; lattice is fixed; no lattice stress
            IBRION=0,  # turns on molecular dynamics
            KBLOCK=100,
            SMASS=0,
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

    def setup(
        self,
        structure: Structure,
        directory: str,
        temperature_start: int = 300,
        temperature_end: int = 1200,
        time_step: float = 2,
        nsteps: int = 10000,
    ):

        # run cleaning and standardizing on structure (based on class attributes)
        structure_cleaned = self._get_clean_structure(structure)

        # write the poscar file
        Poscar.to_file(structure_cleaned, os.path.join(directory, "POSCAR"))

        # Combine our base incar settings with those of our parallelization settings
        # and then write the incar file. Note, we update the values of this incar,
        # so we make a copy of the dict.
        incar = self.incar.copy()
        incar["TEBEG"] = temperature_start
        incar["TEEND"] = temperature_end
        incar["POTIM"] = time_step
        incar["NSW"] = nsteps
        incar = Incar(**incar) + Incar(**self.incar_parallel_settings)
        incar.to_file(
            filename=os.path.join(directory, "INCAR"),
            structure=structure,
        )

        # if KSPACING is not provided in the incar AND kpoints is attached to this
        # class instance, then we write the KPOINTS file
        if self.kpoints and ("KSPACING" not in self.incar):
            Kpoints.to_file(
                structure,
                self.kpoints,
                os.path.join(directory, "KPOINTS"),
            )

        # write the POTCAR file
        Potcar.to_file_from_type(
            structure.composition.elements,
            self.functional,
            os.path.join(directory, "POTCAR"),
            self.potcar_mappings,
        )
