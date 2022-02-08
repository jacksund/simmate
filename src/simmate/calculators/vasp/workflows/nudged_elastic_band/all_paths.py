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

from prefect import apply_map, unmapped

from simmate.workflow_engine.workflow import (
    Workflow,
    task,
    Parameter,
    ModuleStorage,
)
from simmate.workflows.common_tasks import (
    LoadInputAndRegister,
    parse_multi_command,
)
from simmate.calculators.vasp.workflows.nudged_elastic_band.utilities import (
    BuildDiffusionAnalysisTask,
)
from simmate.calculators.vasp.workflows.relaxation import (
    mit_workflow as relaxation_mit_workflow,
)
from simmate.calculators.vasp.workflows.energy import (
    mit_workflow as energy_mit_workflow,
)
from simmate.calculators.vasp.workflows.nudged_elastic_band.single_path import (
    workflow as neb_workflow,
)


from simmate.calculators.vasp.database.nudged_elastic_band import (
    MITDiffusionAnalysis,
)

# Convert our workflow objects to task objects
relax_bulk = relaxation_mit_workflow.to_workflow_task()
energy_bulk = energy_mit_workflow.to_workflow_task()
run_neb = neb_workflow.to_workflow_task()

# Extra setup tasks
load_input_and_register = LoadInputAndRegister()  # TODO: make DiffusionAnalysis a calc?
build_db = BuildDiffusionAnalysisTask(MITDiffusionAnalysis)

# ------------------------

# TODO: Prefect isn't able to do this for-loop. I may need to ask them how
# to map this kind of input. Hopefully this changes with Prefect Orion. This is
# the code that would be in the workflow context:
#
# for i, hop_id in enumerate(migration_hop_ids):
#     run_neb(
#         migration_hop={
#             "migration_hop_table": "MITMigrationHop",
#             "migration_hop_id": hop_id,
#         },
#         directory=directory_cleaned
#         + os.path.sep
#         + f"migration_hop_{i}",
#         source="DistinctPathFinder",
#         diffusion_analysis_id=None,
#         migration_hop_id=None,
#         command=subcommands["command_supercell"] + ";" + subcommands["command_neb"]
#     )
#
# Instead I need these hacky task objects and code.


@task
def get_dir_name(number: int, directory: str):
    number_fill = str(number).zfill(2)
    return os.path.join(directory, f"migration_hop_{number_fill}")


def map_neb(migration_hop_id: int, directory: str, subcommands: dict):

    # !!! This should pass the mapping index... not id. Not sure how to
    # enumerate this with Prefect.
    hop_directory = get_dir_name(migration_hop_id, directory)

    mapped_neb_task = run_neb(
        migration_hop={
            "migration_hop_table": "MITMigrationHop",
            "migration_hop_id": migration_hop_id,
        },
        directory=hop_directory,
        # source="DistinctPathFinder",
        diffusion_analysis_id=None,
        migration_hop_id=migration_hop_id,
        command=subcommands["command_supercell"] + ";" + subcommands["command_neb"],
    )
    return mapped_neb_task


# ------------------------


with Workflow("NEB (for all unique pathways)") as workflow:

    structure = Parameter("structure")
    migrating_specie = Parameter("migrating_specie")
    source = Parameter("source", default=None)
    directory = Parameter("directory", default=None)
    # assume use_previous_directory=False for this flow

    # I separate these out because each calculation is a very different scale.
    # For example, you may want to run the bulk relaxation on 10 cores, the
    # supercell on 50, and the NEB on 200. Even though more cores are available,
    # running smaller calculation on more cores could slow down the calc.
    command = Parameter("command", default="vasp_std > vasp.out")
    # command list expects three subcommands:
    #   command_bulk, command_supercell, and command_neb
    subcommands = parse_multi_command(
        command,
        commands_out=["command_bulk", "command_supercell", "command_neb"],
    )

    # Load our input and make a base directory for all other workflows to run
    # within for us.
    structure_toolkit, directory_cleaned = load_input_and_register(
        input_obj=structure,
        source=source,
        directory=directory,
    )

    # Our step is to run a relaxation on the bulk structure and it uses our inputs
    # directly. The remaining one tasks pass on results.
    run_id_00 = relax_bulk(
        structure=structure_toolkit,
        command=subcommands["command_bulk"],
        directory=directory_cleaned + os.path.sep + "bulk_relaxation",
    )

    # A static energy calculation on the relaxed structure. This isn't necessarily
    # required for NEB, but it takes very little time.
    run_id_01 = energy_bulk(
        structure={
            "calculation_table": "MITRelaxation",
            "directory": run_id_00["directory"],
            "structure_field": "structure_final",
        },
        command=subcommands["command_bulk"],
        directory=directory_cleaned + os.path.sep + "bulk_static_energy",
    )

    # This step does NOT run any calculation, but instead, identifies all
    # diffusion pathways and builds the necessary database entries.
    migration_hop_ids = build_db(
        structure={
            "calculation_table": "MITStaticEnergy",
            "directory": run_id_01["directory"],
        },
        migrating_specie=migrating_specie,
        directory=directory_cleaned,
        vacancy_mode=True,  # assumed for now
    )

    # Run NEB single_path workflow for all these.
    apply_map(
        map_neb,  # the task that we are mapping
        migration_hop_id=migration_hop_ids,  # this input is mapped
        directory=unmapped(directory_cleaned),  # this input will be constant
        subcommands=unmapped(subcommands),  # this input will be constant
    )


workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Diffusion"
# workflow.calculation_table = MITDiffusionAnalysis  # not implemented yet
# workflow.register_kwargs = ["prefect_flow_run_id"]
workflow.result_table = MITDiffusionAnalysis
workflow.s3tasks = [
    relaxation_mit_workflow.s3task,
    energy_mit_workflow.s3task,
] + neb_workflow.s3tasks

workflow.__doc__ = """
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
