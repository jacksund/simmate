# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.workflows.diffusion.utilities import (
    get_migration_images_from_endpoints,
)
from simmate.toolkit.diffusion import MigrationHop
from simmate.workflow_engine import Workflow


class SinglePathWorkflow(Workflow):
    """
    Runs a full diffusion analysis on a single migration hop using NEB.

    Typically, this workflow is not ran directly -- but instead, you would
    use diffusion/all-paths which submits a series of this workflow for you.

    For a given migration path, supercell structures are generated for
    the start and end points of the migration, where vacancy-based diffsion
    is used. These supercells are relaxed using the relaxation/neb-endpoint
    workflow and then interpolated to generate 7 images. These 7 images are
    then relaxed using NEB within the diffusion/from-images workflow.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - relaxation/neb-endpoint (for both start and end supercells)
        - a mini task that interpolated relaxed endpoints and makes images
        - diffusion/from-images

    Currently, this workflow will not run through the command-line, as we
    have not implemented a file format for MigrationHop's yet.
    """

    use_database = False

    endpoint_relaxation_workflow: Workflow = None
    from_images_workflow: Workflow = None

    # TODO:
    # commands_out=["command_supercell", "command_neb"]

    @classmethod
    def run_config(
        cls,
        migration_hop: MigrationHop,
        directory: Path = None,
        source: dict = None,
        command: str = None,
        # These help link results to a higher-level table.
        diffusion_analysis_id: int = None,
        migration_hop_id: int = None,
        # TODO: Can the hop id be inferred from the migration_hop or somewhere
        # else in this context? Maybe even load_input_and_register will use
        # prefect id once it's a Calculation?
        is_restart: bool = False,
        # parameters for supercell and image generation
        nimages: int = 5,
        min_atoms: int = 80,
        max_atoms: int = 240,
        min_length: float = 10,
        **kwargs,
    ):

        # get the supercell endpoint structures
        supercell_start, supercell_end, _ = migration_hop.get_sc_structures(
            min_atoms=min_atoms,
            max_atoms=max_atoms,
            min_length=min_length,
            vac_mode=True,
        )

        # Relax the starting supercell structure
        endpoint_start_state = cls.endpoint_relaxation_workflow.run(
            structure=supercell_start,
            command=command,  # subcommands["command_supercell"]
            directory=directory / f"{cls.endpoint_relaxation_workflow.name_full}.start",
            is_restart=is_restart,
        )

        # Relax the ending supercell structure
        endpoint_end_state = cls.endpoint_relaxation_workflow.run(
            structure=supercell_end,
            command=command,  # subcommands["command_supercell"]
            directory=directory / f"{cls.endpoint_relaxation_workflow.name_full}.end",
            is_restart=is_restart,
        )

        # wait for the endpoint relaxations to finish
        endpoint_start_result = endpoint_start_state.result()
        endpoint_end_result = endpoint_end_state.result()

        images = get_migration_images_from_endpoints(
            supercell_start={
                "database_table": cls.endpoint_relaxation_workflow.database_table.table_name,
                "directory": endpoint_start_result["directory"],
                "structure_field": "structure_final",
            },
            supercell_end={
                "database_table": cls.endpoint_relaxation_workflow.database_table.table_name,
                "directory": endpoint_end_result["directory"],
                "structure_field": "structure_final",
            },
            nimages=nimages,
        )

        # Run NEB on this set of images
        neb_state = cls.from_images_workflow.run(
            migration_images=images,
            command=command,  # subcommands["command_neb"]
            source=source,
            directory=directory,
            diffusion_analysis_id=diffusion_analysis_id,
            migration_hop_id=migration_hop_id,
            is_restart=is_restart,
        )
