# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)
from simmate.workflow_engine.common_tasks import (
    load_input_and_register,
    parse_multi_command,
)

from simmate.calculators.vasp.workflows.nudged_elastic_band.utilities import (
    get_migration_images_from_endpoints,
)
from simmate.calculators.vasp.workflows.relaxation import (
    neb_endpoint_workflow as relaxation_neb_endpoint_workflow,
)
from simmate.calculators.vasp.workflows.nudged_elastic_band.from_images import (
    workflow as neb_from_images,
)
from simmate.calculators.vasp.database.nudged_elastic_band import (
    MITDiffusionAnalysis,
)

# Convert our workflow objects to task objects
relax_endpoint = relaxation_neb_endpoint_workflow.to_workflow_task()
run_neb = neb_from_images.to_workflow_task()

with Workflow("diffusion/from-endpoints") as workflow:

    supercell_start = Parameter("supercell_start")
    supercell_end = Parameter("supercell_end")
    directory = Parameter("directory", default=None)
    source = Parameter("source", default=None)

    # This helps link to a higher-level table.
    diffusion_analysis_id = Parameter("diffusion_analysis_id", default=None)

    # I separate these out because each calculation is a very different scale.
    # For example, you may want to run the bulk relaxation on 10 cores, the
    # supercell on 50, and the NEB on 200. Even though more cores are available,
    # running smaller calculation on more cores could slow down the calc.
    command = Parameter("command", default="vasp_std > vasp.out")
    # command list expects three subcommands:
    #   command_bulk, command_supercell, and command_neb
    subcommands = parse_multi_command(
        command,
        commands_out=["command_supercell", "command_neb"],
    )

    # Load our input and make a base directory for all other workflows to run
    # within for us.
    parameters_cleaned = load_input_and_register(
        supercell_start=supercell_start,
        supercell_end=supercell_end,
        source=source,
        directory=directory,
        command=command,
        diffusion_analysis_id=diffusion_analysis_id,
    )

    # Relax the starting supercell structure
    run_id_00 = relax_endpoint(
        structure=parameters_cleaned["supercell_start"],
        command=subcommands["command_supercell"],
        directory=parameters_cleaned["directory"]
        + os.path.sep
        + "endpoint_relaxation_start",
    )

    # Relax the ending supercell structure
    run_id_01 = relax_endpoint(
        structure=parameters_cleaned["supercell_end"],
        command=subcommands["command_supercell"],
        directory=parameters_cleaned["directory"]
        + os.path.sep
        + "endpoint_relaxation_end",
    )

    images = get_migration_images_from_endpoints(
        supercell_start={
            "database_table": "MatVirtualLabCINEBEndpointRelaxation",
            "directory": run_id_00["directory"],
            "structure_field": "structure_final",
        },
        supercell_end={
            "database_table": "MatVirtualLabCINEBEndpointRelaxation",
            "directory": run_id_01["directory"],
            "structure_field": "structure_final",
        },
    )

    # Run NEB on this set of images
    run_id_02 = run_neb(
        migration_images=images,
        command=subcommands["command_neb"],
        source=parameters_cleaned["source"],
        directory=parameters_cleaned["directory"],
        diffusion_analysis_id=parameters_cleaned["diffusion_analysis_id"],
    )


workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Diffusion"
workflow.database_table = MITDiffusionAnalysis
workflow.s3tasks = [
    relaxation_neb_endpoint_workflow.s3task,
    neb_from_images.s3task,
]

workflow.description_doc_short = "runs NEB using two endpoint structures as input"
workflow.__doc__ = """
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
