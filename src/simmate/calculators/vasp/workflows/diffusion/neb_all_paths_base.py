# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import DistinctPathFinder
from simmate.workflow_engine import Workflow


class NebAllPathsWorkflow(Workflow):
    """
    Runs a full diffusion analysis on a bulk crystal structure using NEB.

    The bulk structure will be geometry optimized and then
    `simmate.toolkit.diffusion.DistinctPathFinder` is used to find all
    symmetrically unique migration hops in the structure up until the hops
    become percolating (>0-D). For each unique hop, the workflow
    diffusion/single_path is submitted.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - relaxation/mit
        - static-energy/mit
        - a mini task that identifies unique migration hops
        - (for each hop) diffusion/single-path


    The folder tree looks like...

    ```
    # note, folder names will match the workflow used
    simmate-task-12345
        ├── bulk relaxation
        ├── bulk static-energy
        ├── migration hop 00
        ├── migration hop 01
        ...
        └── migration_hop_N  # all migration_hop folders have the same structure
            ├── endpoint relaxation start
            ├── endpoint relaxation end
            ├── 01
            ├── 02
            ├── 03
            ...
            └── N  # corresponds to image number
    ```
    """

    update_database_from_results = False

    bulk_relaxation_workflow: Workflow = None
    bulk_static_energy_workflow: Workflow = None
    single_path_workflow: Workflow = None

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        migrating_specie: str,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        is_restart: bool = False,
        # parameters for supercell and image generation
        nimages: int = 5,
        min_supercell_atoms: int = 80,
        max_supercell_atoms: int = 240,
        min_supercell_vector_lengths: float = 10,
        # extra parameters for distinct path finding
        max_path_length: float = None,
        percolation_mode: str = ">1d",
        vacancy_mode: bool = True,
        run_id: str = None,
        **kwargs,
    ):

        # run a relaxation on the bulk structure
        bulk_relax_result = cls.bulk_relaxation_workflow.run(
            structure=structure,
            command=command,  # subcommands["command_bulk"]
            directory=directory / cls.bulk_relaxation_workflow.name_full,
            is_restart=is_restart,
        ).result()

        # run static energy calculation on the relaxed structure
        bulk_static_energy_result = cls.bulk_static_energy_workflow.run(
            structure=bulk_relax_result,
            command=command,  # subcommands["command_bulk"]
            directory=directory / cls.bulk_static_energy_workflow.name_full,
            is_restart=is_restart,
        ).result()

        # Using the relaxed structure, detect all symmetrically unique paths
        pathfinder = DistinctPathFinder(
            structure=bulk_static_energy_result.to_toolkit(),
            migrating_specie=migrating_specie,
            max_path_length=max_path_length,
            perc_mode=percolation_mode,
        )
        migration_hops = pathfinder.get_paths()

        # Write the paths found so user can preview what's analyzed below
        pathfinder.write_all_migration_hops(directory)

        # load the current database entry so we can link the other runs
        # to it up front
        current_calc = cls.database_table.from_run_context(run_id=run_id)

        # Run NEB single_path workflow for all these.
        for i, hop in enumerate(migration_hops):
            state = cls.single_path_workflow.run(
                # !!! The hop object gives an ugly output. Should I use the
                # database dictionary instead?
                migration_hop=hop,
                directory=directory
                / f"{cls.single_path_workflow.name_full}.{str(i).zfill(2)}",
                command=command,
                # subcommands["command_supercell"]
                # + ";"
                # + subcommands["command_neb"],
                is_restart=is_restart,
                min_atoms=min_supercell_atoms,
                max_atoms=max_supercell_atoms,
                min_length=min_supercell_vector_lengths,
                nimages=nimages,
                vacancy_mode=vacancy_mode,
                diffusion_analysis_id=current_calc.id,
            )
            state.result()  # wait until the job finishes
