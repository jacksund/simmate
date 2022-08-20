# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.workflows.diffusion.utilities import (
    get_migration_images_from_endpoints,
)
from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow


class NebFromEndpointWorkflow(Workflow):
    """
    Runs a full diffusion analysis from a start and end supercell using NEB.

    The input start/end structures will be relaxed using the relaxation/neb-endpoint
    workflow and then interpolated to generate 7 images. These 7 images are
    then relaxed using NEB within the diffusion/from-images workflow.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - relaxation/neb-endpoint (for both start and end supercells)
        - a mini task that interpolated relaxed endpoints and makes images
        - diffusion/from-images

    If you are running this workflow via the command-line, you can run this
    with...

    ``` bash
    simmate workflows run diffusion/all-paths -c "cmd1; cmd2" --supercell_start example1.cif --supercell_end example2.cif
    ```

    Note, the `-c` here is very important! Here we are passing three commands
    separated by semicolons. Each command is passed to a specific workflow call:

        - cmd1 --> used for endpoint supercell relaxations
        - cmd2 --> used for NEB

    Thus, you can scale your resources for each step. Here's a full -c option:

    ```
    -c "mpirun -n 12 vasp_std > vasp.out; mpirun -n 70 vasp_std > vasp.out"
    ```
    """

    description_doc_short = "runs NEB using two endpoint structures as input"

    endpoint_relaxation_workflow: Workflow = None
    from_images_workflow: Workflow = None

    @classmethod
    def run_config(
        cls,
        supercell_start: Structure,
        supercell_end: Structure,
        directory: Path = None,
        source: dict = None,
        command: str = None,
        nimages: int = 5,
        # This helps link results to a higher-level table.
        diffusion_analysis_id: int = None,
        is_restart: bool = False,
        **kwargs,
    ):
        # command list expects three subcommands:
        #   command_bulk, command_supercell, and command_neb
        # subcommands = parse_multi_command(
        #     command,
        #     commands_out=["command_supercell", "command_neb"],
        # )

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

        # interpolate / empirically relax the endpoint structures
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
        ).result()

        # Run NEB on this set of images
        neb_state = cls.from_images_workflow.run(
            migration_images=images,
            command=command,  # subcommands["command_neb"]
            directory=directory,
            diffusion_analysis_id=diffusion_analysis_id,
            is_restart=is_restart,
        )
