# -*- coding: utf-8 -*-

from pathlib import Path

from pymatgen.io.vasp.inputs import Kpoints

from simmate.apps.materials_project.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)
from simmate.apps.vasp.inputs import Incar, Poscar, Potcar
from simmate.apps.vasp.workflows.electronic_structure import get_hse_kpoints
from simmate.toolkit import Structure


class VaspDensityOfStates(StaticEnergy__Vasp__Matproj):
    """
    A base class for density of states (DOS) calculations. This is not meant
    to be used directly but instead should be inherited from.

    This is also a non self-consistent field (non-SCF) calculation and thus uses
    the a fixed charge density from a previous static energy calculation.
    """

    use_previous_directory = True
    required_files = StaticEnergy__Vasp__Matproj.required_files + ["CHGCAR"]

    @classmethod
    def setup(cls, directory: Path, structure: Structure, **kwargs):
        # run cleaning and standardizing on structure (based on class attributes)
        structure_cleaned = cls._get_clean_structure(structure, **kwargs)

        # write the poscar file
        Poscar.to_file(structure_cleaned, directory / "POSCAR")

        # Combine our base incar settings with those of our parallelization settings
        # and then write the incar file
        incar = Incar(**cls.incar)
        incar.to_file(
            filename=directory / "INCAR",
            structure=structure_cleaned,
        )

        ##############
        # we need to find the high-symmetry Kpt path. Note that all of this
        # functionality will be moved to the KptPath class and then extended to
        # vasp.inputs.kpoints class. Until those classes are ready, we just use
        # pymatgen here.
        if incar.get("LHFCALC", False):
            kpoints = get_hse_kpoints(structure_cleaned, mode="uniform")
        elif cls.kpoints and ("KSPACING" not in cls.incar):
            Kpoints.to_file(
                structure_cleaned,
                cls.kpoints,
                directory / "KPOINTS",
            )
        else:
            kpoints = None
        if kpoints:
            kpoints.write_file(directory / "KPOINTS")
        ##############

        # write the POTCAR file
        Potcar.to_file_from_type(
            structure_cleaned.composition.elements,
            cls.functional,
            directory / "POTCAR",
            cls.potcar_mappings,
        )
