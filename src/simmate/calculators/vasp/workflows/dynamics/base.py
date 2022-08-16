# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.inputs import Incar, Kpoints, Poscar, Potcar
from simmate.calculators.vasp.workflows.base import VaspWorkflow
from simmate.toolkit import Structure


class DynamicsWorkflow(VaspWorkflow):
    @classmethod
    def setup(
        cls,
        structure: Structure,
        directory: Path,
        temperature_start: int = 300,
        temperature_end: int = 1200,
        time_step: float = 2,
        nsteps: int = 10000,
        **kwargs,
    ):

        # run cleaning and standardizing on structure (based on class attributes)
        structure_cleaned = cls._get_clean_structure(structure, **kwargs)

        # write the poscar file
        Poscar.to_file(structure_cleaned, directory / "POSCAR")

        # Combine our base incar settings with those of our parallelization settings
        # and then write the incar file. Note, we update the values of this incar,
        # so we make a copy of the dict.
        incar = cls.incar.copy()
        incar["TEBEG"] = temperature_start
        incar["TEEND"] = temperature_end
        incar["NSW"] = nsteps
        incar["POTIM"] = time_step
        incar = Incar(**incar) + Incar(**cls.incar_parallel_settings)
        incar.to_file(
            filename=directory / "INCAR",
            structure=structure,
        )

        # if KSPACING is not provided in the incar AND kpoints is attached to this
        # class instance, then we write the KPOINTS file
        if cls.kpoints and ("KSPACING" not in cls.incar):
            Kpoints.to_file(
                structure,
                cls.kpoints,
                directory / "KPOINTS",
            )

        # write the POTCAR file
        Potcar.to_file_from_type(
            structure.composition.elements,
            cls.functional,
            directory / "POTCAR",
            cls.potcar_mappings,
        )
