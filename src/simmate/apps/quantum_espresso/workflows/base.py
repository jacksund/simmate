# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.apps.quantum_espresso.inputs import PwscfInput
from simmate.apps.quantum_espresso.inputs.k_points import Kpoints
from simmate.apps.quantum_espresso.inputs.potentials_sssp import (
    SSSP_PBE_EFFICIENCY_MAPPINGS,
    SSSP_PBE_PRECISION_MAPPINGS,
)
from simmate.configuration import settings
from simmate.engine import S3Workflow
from simmate.toolkit import Structure
from simmate.utilities import get_docker_command
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
#!!! move this to utilities
from simmate.apps.vasp.workflows.base import check_for_standardization_bugs

# TODO: add StructureInputWorkflow mixin which can be made from VaspWorkflow class
class PwscfWorkflow(S3Workflow):
    required_files = ["pwscf.in"]

    command: str = settings.quantum_espresso.default_command
    """
    The command to call PW-SCF, which is typically `pw.x`.
    
    The typical default is "pw.x < pwscf.in > pw-scf.out"
    """

    # -------------------------------------------------------------------------

    # We set each section of PW-SCF's input parameters as a class attribute
    # https://www.quantum-espresso.org/Doc/INPUT_PW.html

    control: dict = {}
    """
    key-value pairs for the `&CONTROL` section of `pwscf.in`
    """

    system: dict = {}
    """
    key-value pairs for the `&SYSTEM` section of `pwscf.in`
    """

    electrons: dict = {}
    """
    key-value pairs for the `&ELECTRONS` section of `pwscf.in`
    """

    ions: dict = {}
    """
    key-value pairs for the `&IONS` section of `pwscf.in`
    """

    cell: dict = {}
    """
    key-value pairs for the `&CELL` section of `pwscf.in`
    """

    fcp: dict = {}
    """
    key-value pairs for the `&FCP` section of `pwscf.in`
    """

    rism: dict = {}
    """
    key-value pairs for the `&RISM` section of `pwscf.in`
    """
    
    standardize_structure: str | bool = False
    """
    In some cases, we may want to standardize the structure during our setup().
    
    This means running symmetry analysis on the structure in order to reduce
    the symmetry and also converting it to some standardized form. There
    are three different forms to choose from and thus 3 different values that
    `standardize_structure` can be set to:
    
    - `primitive`: for the standard primitive unitcell
    - `conventional`: for the standard conventional unitcell
    - `primitive-LLL`: for the standard primitive unitcell that is then LLL-reduced
    - `False`: this is the default and will disable this feature
    
    We recommend using `primitive-LLL` when the smallest possible and most cubic
    unitcell is desired.
    
    We recommend using `primitive` when calculating band structures and 
    ensuring we have a standardized high-symmetry path. Note, existing band
    structure workflows automatically adjust this value for you.
    
    To control the tolerances used to symmetrize the structure, you can use the
    symmetry_precision and angle_tolerance attributes.
    
    By default, no standardization is applied.
    """

    symmetry_precision: float = 0.01
    """
    If standardize_structure=True, then this is the cutoff value used to determine
    if the sites are symmetrically equivalent. (in Angstroms)
    """

    angle_tolerance: float = 0.5
    """
    If standardize_structure=True, then this is the cutoff value used to determine
    if the angles between sites are symmetrically equivalent. (in Degrees)
    """

    @classmethod
    @property
    def full_settings(cls) -> dict:
        # TODO: consider making this use PwscfInput class
        return dict(
            control=cls.control,
            system=cls.system,
            electrons=cls.electrons,
            ions=cls.ions,
            fcp=cls.fcp,
            rism=cls.rism,
        )

    # -------------------------------------------------------------------------

    psuedo_mappings_set: str = None
    """
    Indicates which psuedopotentials mappings to use (in the `psuedo_mappings` attribute).
    Can be either 'SSSP_PBE_PRECISION' or 'SSSP_PBE_EFFICIENCY'
    """

    @classmethod
    @property
    def psuedo_mappings(cls) -> dict:
        if cls.psuedo_mappings_set == "SSSP_PBE_PRECISION":
            return SSSP_PBE_PRECISION_MAPPINGS
        elif cls.psuedo_mappings_set == "SSSP_PBE_EFFICIENCY":
            return SSSP_PBE_EFFICIENCY_MAPPINGS
        else:
            raise Exception(
                f"Unknown psuedo_mappings_set provided: {cls.psuedo_mappings_set}"
            )

    # -------------------------------------------------------------------------

    k_points: dict = {}
    """
    Configuration for generating the k-points grid for each input. This
    config is passed to `Kpoints.from_dynamic`
    """

    # -------------------------------------------------------------------------
    # !!! This is a copy of the equivalent method for vasp workflows. Move to
    # utilities?
    @classmethod
    def _get_clean_structure(
        cls,
        structure: Structure,
        standardize_structure: str | bool = None,
        symmetry_precision: float = None,
        angle_tolerance: float = None,
        **kwargs,
    ) -> Structure:
        """
        Uses the class attribute for `standardize_structure`. If this is set
        to any of the listed modes, then the structure unitcell is converted
        using the proper methods.

        Note, this method is typically called within `setup` before any input
        files are written. You should never have to call it directly.
        """

        # See if these values were provided, or default to class attribute.
        # We rename this to "standardize mode" to accurately descibe the
        # variable if it is set
        standardize_mode = standardize_structure or cls.standardize_structure
        symmetry_precision = symmetry_precision or cls.symmetry_precision
        angle_tolerance = angle_tolerance or cls.angle_tolerance

        # if standardize_structure is not requested, then we just return the
        # orignal input structure.
        if not standardize_mode:
            return structure

        # Make sure the user
        if standardize_mode not in ["primitive-LLL", "conventional", "primitive"]:
            raise Exception(
                f"Standardization mode {standardize_mode} is not supported."
            )

        # Both cleaning steps start with looking at the symmetry analysis
        sym_finder = SpacegroupAnalyzer(
            structure,
            symprec=symmetry_precision,
            angle_tolerance=angle_tolerance,
        )

        # If requested, we convert to the LLL-reduced unit cell, which aims to
        # be as cubic as possible.
        if standardize_mode == "primitive-LLL":
            structure_prim = sym_finder.get_primitive_standard_structure()
            structure_cleaned = structure_prim.copy(sanitize=True)
            return structure_cleaned

        # For band structures, we need to make sure the structure is in the
        # standardized primitive form.
        if standardize_mode == "primitive":
            structure_cleaned = sym_finder.get_primitive_standard_structure(
                international_monoclinic=False,
            )
            # check for pymatgen bugs here
            check_for_standardization_bugs(structure, structure_cleaned)
            return structure_cleaned

        # lastly is the conventional standard, which is used the least.
        if standardize_mode == "conventional":
            structure_cleaned = sym_finder.get_conventional_standard_structure()
            return structure_cleaned
    
    @classmethod
    def setup(cls, directory: Path, structure: Structure, **kwargs):
        # run cleaning and standardizing on structure (based on class attributes)
        structure_cleaned = cls._get_clean_structure(structure, **kwargs)

        input_config = PwscfInput(
            structure=structure_cleaned,
            kpoints=Kpoints.from_dynamic(
                k_points=cls.k_points,
                structure=structure,
            ),
            psuedo_mappings=cls.psuedo_mappings,
            control=cls.control,
            system=cls.system,
            electrons=cls.electrons,
            ions=cls.ions,
            cell=cls.cell,
            fcp=cls.fcp,
            rism=cls.rism,
        )
        input_config.to_file(directory / "pwscf.in")

    @classmethod
    def get_final_command(
        cls,
        command: str = None,
        directory: Path = None,
        **kwargs,
    ) -> str:
        input_command = command if command else cls.command
        if settings.quantum_espresso.docker.enable == True:
            final_command = get_docker_command(
                image=settings.quantum_espresso.docker.image,
                inner_command=input_command,
                # BUG FIX If the directory has a space (e.g. OneDrive - University...)
                # docker will throw an error. wrapping with directory with
                # "" solves the issue (but wrapping with '' doesn't)
                volumes=[
                    f'"{str(directory)}":/qe_calc',
                    f'"{str(settings.quantum_espresso.psuedo_dir)}":/potentials',
                ],
            )
            return final_command
        else:
            return input_command

    # -------------------------------------------------------------------------

