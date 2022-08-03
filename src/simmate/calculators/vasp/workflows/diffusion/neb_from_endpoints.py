# -*- coding: utf-8 -*-

import os

from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow
from simmate.workflow_engine.common_tasks import (
    load_input_and_register,
    parse_multi_command,
)

from simmate.calculators.vasp.workflows.diffusion.utilities import (
    get_migration_images_from_endpoints,
)
from simmate.calculators.vasp.workflows.relaxation.neb_endpoint import (
    Relaxation__Vasp__NebEndpoint,
)
from simmate.calculators.vasp.workflows.diffusion.neb_from_images import (
    Diffusion__Vasp__NebFromImages,
)
from simmate.calculators.vasp.database.nudged_elastic_band import (
    MITDiffusionAnalysis,
)


class Diffusion__Vasp__NebFromEndpoints(Workflow):
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

    database_table = MITDiffusionAnalysis

    description_doc_short = "runs NEB using two endpoint structures as input"

    @classmethod
    def run_config(
        cls,
        supercell_start: Structure,
        supercell_end: Structure,
        directory: str = None,
        source: dict = None,
        command: str = None,
        # This helps link results to a higher-level table.
        diffusion_analysis_id: int = None,
        is_restart: bool = False,
    ):

        # command list expects three subcommands:
        #   command_bulk, command_supercell, and command_neb
        subcommands = parse_multi_command(
            command,
            commands_out=["command_supercell", "command_neb"],
        )
        # I separate these out because each calculation is a very different scale.
        # For example, you may want to run the bulk relaxation on 10 cores, the
        # supercell on 50, and the NEB on 200. Even though more cores are available,
        # running smaller calculation on more cores could slow down the calc.

        # Load our input and make a base directory for all other workflows to run
        # within for us.
        parameters_cleaned = load_input_and_register(
            supercell_start=supercell_start,
            supercell_end=supercell_end,
            source=source,
            directory=directory,
            command=command,
            diffusion_analysis_id=diffusion_analysis_id,
            is_restart=is_restart,
        ).result()

        # Relax the starting supercell structure
        endpoint_start_state = Relaxation__Vasp__NebEndpoint.run(
            structure=supercell_start,
            command=subcommands["command_supercell"],
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + f"{Relaxation__Vasp__NebEndpoint.name_full}.start",
            is_restart=is_restart,
        )

        # Relax the ending supercell structure
        endpoint_end_state = Relaxation__Vasp__NebEndpoint.run(
            structure=supercell_end,
            command=subcommands["command_supercell"],
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + f"{Relaxation__Vasp__NebEndpoint.name_full}.end",
            is_restart=is_restart,
        )

        # wait for the endpoint relaxations to finish
        endpoint_start_result = endpoint_start_state.result()
        endpoint_end_result = endpoint_end_state.result()

        # interpolate / empirically relax the endpoint structures
        images = get_migration_images_from_endpoints(
            supercell_start={
                "database_table": Relaxation__Vasp__NebEndpoint.database_table.__name__,
                "directory": endpoint_start_result["directory"],
                "structure_field": "structure_final",
            },
            supercell_end={
                "database_table": Relaxation__Vasp__NebEndpoint.database_table.__name__,
                "directory": endpoint_end_result["directory"],
                "structure_field": "structure_final",
            },
        ).result()

        # Run NEB on this set of images
        neb_state = Diffusion__Vasp__NebFromImages.run(
            migration_images=images,
            command=subcommands["command_neb"],
            source=parameters_cleaned["source"],
            directory=parameters_cleaned["directory"],
            diffusion_analysis_id=parameters_cleaned["diffusion_analysis_id"],
            is_restart=is_restart,
        )
