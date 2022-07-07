# -*- coding: utf-8 -*-

"""
Runs a NEB on all unique pathways within a structure. 

The folder tree looks like...
```
simmate-task-12345/  # determined by simmate.utilities.get_directory
    ├── bulk_relaxation
    ├── bulk_static_energy
    ├── migration_hop_00
    ├── migration_hop_01
    ...
    └── migration_hop_N  # all migration_hop folders have the same structure
        ├── endpoint_relaxation_start
        ├── endpoint_relaxation_end
        ├── 01
        ├── 02
        ├── 03
        ...
        └── N  # corresponds to image number
```
"""

import os

from simmate.toolkit import Structure
from simmate.workflow_engine.workflow import Workflow
from simmate.workflow_engine.common_tasks import (
    load_input_and_register,
    parse_multi_command,
)
from simmate.calculators.vasp.workflows.nudged_elastic_band.utilities import (
    BuildDiffusionAnalysisTask,
)
from simmate.calculators.vasp.workflows.relaxation.mit import Relaxation__Vasp__Mit
from simmate.calculators.vasp.workflows.static_energy.mit import StaticEnergy__Vasp__Mit
from simmate.calculators.vasp.workflows.nudged_elastic_band.single_path import (
    Diffusion__Vasp__SinglePath,
)
from simmate.calculators.vasp.database.nudged_elastic_band import (
    MITDiffusionAnalysis,
)


class Diffusion__Vasp__NEBAllPaths(Workflow):
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

    If you are running this workflow via the command-line, you can run this
    with...

    ``` bash
    simmate workflows run diffusion/all-paths -s example.cif -c "cmd1; cmd2; cmd3"
    ```

    Note, the `-c` here is very important! Here we are passing three commands
    separated by semicolons. Each command is passed to a specific workflow call:

        - cmd1 --> used for bulk crystal relaxation and static energy
        - cmd2 --> used for endpoint supercell relaxations
        - cmd3 --> used for NEB

    Thus, you can scale your resources for each step. Here's a full -c option:

    -c "vasp_std > vasp.out; mpirun -n 12 vasp_std > vasp.out; mpirun -n 70 vasp_std > vasp.out"
    """

    database_table = MITDiffusionAnalysis

    description_doc_short = "runs NEB for all symmetrically unique paths"

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        migrating_specie: str,
        command: str = None,
        source: dict = None,
        directory: str = None,
    ):
        # command list expects three subcommands:
        #   command_bulk, command_supercell, and command_neb
        #
        # I separate these out because each calculation is a very different scale.
        # For example, you may want to run the bulk relaxation on 10 cores, the
        # supercell on 50, and the NEB on 200. Even though more cores are available,
        # running smaller calculation on more cores could slow down the calc.
        subcommands = parse_multi_command(
            command,
            commands_out=["command_bulk", "command_supercell", "command_neb"],
        )

        # Load our input and make a base directory for all other workflows to run
        # within for us.
        parameters_cleaned = load_input_and_register(
            structure=structure,
            source=source,
            directory=directory,
            command=command,
            migrating_specie=migrating_specie,
            register_run=False,
        )

        # Our step is to run a relaxation on the bulk structure and it uses our inputs
        # directly. The remaining one tasks pass on results.
        bulk_relax_result = Relaxation__Vasp__Mit.run(
            structure=parameters_cleaned["structure"],
            command=subcommands["command_bulk"],
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + Relaxation__Vasp__Mit.name_full,
        ).result()

        # A static energy calculation on the relaxed structure. This isn't necessarily
        # required for NEB, but it takes very little time.
        bulk_static_energy_result = StaticEnergy__Vasp__Mit(
            structure={
                "database_table": Relaxation__Vasp__Mit.database_table.__name__,
                "directory": bulk_relax_result["directory"],
                "structure_field": "structure_final",
            },
            command=subcommands["command_bulk"],
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + StaticEnergy__Vasp__Mit.name_full,
        ).result()

        # This step does NOT run any calculation, but instead, identifies all
        # diffusion pathways and builds the necessary database entries.
        build_db = BuildDiffusionAnalysisTask(MITDiffusionAnalysis)
        migration_hop_ids = build_db(
            structure={
                "database_table": StaticEnergy__Vasp__Mit.database_table.__name__,
                "directory": bulk_static_energy_result["directory"],
            },
            migrating_specie=migrating_specie,
            directory=parameters_cleaned["directory"],
            vacancy_mode=True,  # assumed for now
        )

        # Run NEB single_path workflow for all these.
        for i, hop_id in enumerate(migration_hop_ids):
            Diffusion__Vasp__SinglePath.run(
                migration_hop={
                    "migration_hop_table": "MITMigrationHop",
                    "migration_hop_id": hop_id,
                },
                directory=parameters_cleaned["directory"]
                + os.path.sep
                + f"migration_hop_{i}",
                source="DistinctPathFinder",
                diffusion_analysis_id=None,
                migration_hop_id=None,
                command=subcommands["command_supercell"]
                + ";"
                + subcommands["command_neb"],
            )  # don't block on results to allow parallel runs
