# -*- coding: utf-8 -*-

import os
from typing import Tuple

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import MigrationHop

# TODO: use MigrationImages use to generate images?

from simmate.workflow_engine import Workflow, task
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


class Diffusion__Vasp__NebSinglePath(Workflow):
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

    database_table = MITDiffusionAnalysis
    description_doc_short = "runs NEB using a MigrationHop object as input"

    @classmethod
    def run_config(
        cls,
        migration_hop: MigrationHop,
        directory: str = None,
        source: dict = None,
        command: str = None,
        # These help link results to a higher-level table.
        diffusion_analysis_id: int = None,
        migration_hop_id: int = None,
        # TODO: Can the hop id be inferred from the migration_hop or somewhere
        # else in this context? Maybe even load_input_and_register will use
        # prefect id once it's a Calculation?
        is_restart: bool = False,
    ):

        # split the command if separate ones were given
        subcommands = parse_multi_command(
            command,
            commands_out=["command_supercell", "command_neb"],
        ).result()

        # Load our input and make a base directory for all other workflows to run
        # within for us.
        parameters_cleaned = load_input_and_register(
            migration_hop=migration_hop,
            source=source,
            directory=directory,
            command=command,
            diffusion_analysis_id=diffusion_analysis_id,
            migration_hop_id=migration_hop_id,
            is_restart=is_restart,
            register_run=False,
        ).result()

        # get the supercell endpoint structures
        supercell_start, supercell_end = get_endpoint_structures(
            parameters_cleaned["migration_hop"]
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
            diffusion_analysis_id=diffusion_analysis_id,
            migration_hop_id=migration_hop_id,
            is_restart=is_restart,
        )


@task
def get_endpoint_structures(migration_hop: MigrationHop) -> Tuple[Structure]:
    """
    Simple wrapper for get_sc_structures method that makes it a Prefect task.
    I assume parameters for now
    """
    start_supercell, end_supercell, _ = migration_hop.get_sc_structures(
        # min_atoms=10,
        # max_atoms=50,
        # min_length=5,
        vac_mode=True,
    )
    try:
        assert start_supercell != end_supercell
    except:
        raise Exception(
            "This structure has a bug due to a rounding error. "
            "Our team is aware of this bug and it has been fixed for the next "
            "pymatgen-analysis-diffusion release."
        )
    return start_supercell, end_supercell
