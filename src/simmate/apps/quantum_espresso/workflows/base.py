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

    @classmethod
    def setup(cls, directory: Path, structure: Structure, **kwargs):
        # run cleaning and standardizing on structure (based on class attributes)
        # TODO: structure_cleaned = cls._get_clean_structure(structure, **kwargs)

        input_config = PwscfInput(
            structure=structure,
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
        cls, command: str = None, directory: Path = None, **kwargs
    ) -> str:
        # EXPERIMENTAL - some of this functionality will likely move to S3Workflow
        if settings.quantum_espresso.docker.use == True:
            final_command = get_docker_command(
                image=settings.quantum_espresso.docker.image,
                entrypoint=command,
                volumes=[
                    f"{str(directory)}:/qe_calc",
                    f"{str(settings.quantum_espresso.psuedo_dir)}:/potentials",
                ],
            )
        breakpoint()
        return final_command

    # -------------------------------------------------------------------------
