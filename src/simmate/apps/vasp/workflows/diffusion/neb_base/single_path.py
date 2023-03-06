# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.engine import Workflow
from simmate.toolkit import Structure
from simmate.toolkit.diffusion import MigrationHop, MigrationImages
from simmate.toolkit.diffusion.utilities import clean_start_end_images


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

    endpoint_relaxation_workflow: Workflow = None
    endpoint_energy_workflow: Workflow = None
    from_images_workflow: Workflow = None

    # Oddly enough, the from_images_workflow and this workflow share a table
    # entry, so nothing needs to be done for working up results. See
    # how we pass run_id=run_id below.
    update_database_from_results = False

    @classmethod
    def run_config(
        cls,
        migration_hop: MigrationHop,
        directory: Path = None,
        source: dict = None,
        command: str = None,
        diffusion_analysis_id: int = None,
        is_restart: bool = False,
        relax_endpoints: bool = True,
        # parameters for supercell and image generation
        nimages: int = 5,
        min_atoms: int = 80,
        max_atoms: int = 240,
        min_length: float = 10,
        run_id: str = None,
        **kwargs,
    ):
        # get the supercell endpoint structures
        supercell_start, supercell_end, _ = migration_hop.get_sc_structures(
            min_atoms=min_atoms,
            max_atoms=max_atoms,
            min_length=min_length,
            vac_mode=True,
        )

        # BUG-CHECK to ensure sites are in proper order
        # Consider moving this check into the get_sc_structures method.
        supercell_start, supercell_end = clean_start_end_images(
            supercell_start,
            supercell_end,
        )
        ## end bugcheck

        if relax_endpoints:
            # Relax the starting supercell structure
            endpoint_start_state = cls.endpoint_relaxation_workflow.run(
                structure=supercell_start,
                command=command,  # subcommands["command_supercell"]
                directory=directory
                / f"{cls.endpoint_relaxation_workflow.name_full}.start",
                is_restart=is_restart,
            )

            # Relax the ending supercell structure
            endpoint_end_state = cls.endpoint_relaxation_workflow.run(
                structure=supercell_end,
                command=command,  # subcommands["command_supercell"]
                directory=directory
                / f"{cls.endpoint_relaxation_workflow.name_full}.end",
                is_restart=is_restart,
            )

            # wait for the endpoint relaxations to finish and use them to
            # update the structures we are using
            supercell_start = endpoint_start_state.result()
            supercell_end = endpoint_end_state.result()

        # Run static-energy calculations for the endpoints
        start_energy = cls.endpoint_energy_workflow.run(
            structure=supercell_start,
            command=command,  # subcommands["command_supercell"]
            directory=directory / f"{cls.endpoint_energy_workflow.name_full}.start",
            is_restart=is_restart,
        )
        end_energy = cls.endpoint_energy_workflow.run(
            structure=supercell_end,
            command=command,  # subcommands["command_supercell"]
            directory=directory / f"{cls.endpoint_energy_workflow.name_full}.end",
            is_restart=is_restart,
        )
        supercell_start = start_energy.result()
        supercell_end = end_energy.result()

        # use the endpoints to generate intermediate images
        # Make sure we have toolkit objects, and if not, convert them
        supercell_start_cleaned = Structure.from_dynamic(supercell_start)
        supercell_end_cleaned = Structure.from_dynamic(supercell_end)
        # Then generate the images
        images = MigrationImages.from_endpoints(
            structure_start=supercell_start_cleaned,
            structure_end=supercell_end_cleaned,
            nimages=nimages,
            # TODO: Add extra IDPP relaxation parameters and an option to disable it
            # relaxation to the diffusing species here.
            # species=[migration_hop.isite.specie.symbol],
            # sort_tol=0,  # sites in our structures should already be sortedw
            # idpp_relax=False,
        )

        # Run NEB on this set of images
        neb_state = cls.from_images_workflow.run(
            migration_images=images,
            command=command,  # subcommands["command_neb"]
            source=source,
            directory=directory,
            diffusion_analysis_id=diffusion_analysis_id,
            is_restart=is_restart,
            # Run id is very important here as it tells the underlying
            # workflow that it doesn't need to create a new database object
            # during registration -- as it will use the one that was registered
            # when this workflow started. This is also why we have a dummy
            # `update_database_from_results` method below
            run_id=run_id,
        )
        neb_images = neb_state.result()
