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
    get_endpoint_structures,
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


with Workflow("diffusion/single-path") as workflow:

    migration_hop = Parameter("migration_hop")
    directory = Parameter("directory", default=None)
    source = Parameter("source", default=None)

    # This helps link to a higher-level table.
    diffusion_analysis_id = Parameter("diffusion_analysis_id", default=None)
    # TODO: Can the hop id be inferred from the migration_hop or somewhere
    # else in this context? Maybe even load_input_and_register will use
    # prefect id once it's a Calculation?
    migration_hop_id = Parameter("migration_hop_id", default=None)

    command = Parameter("command", default="vasp_std > vasp.out")
    subcommands = parse_multi_command(
        command,
        commands_out=["command_supercell", "command_neb"],
    )

    # Load our input and make a base directory for all other workflows to run
    # within for us.
    parameters_cleaned = load_input_and_register(
        migration_hop=migration_hop,
        source=source,
        directory=directory,
        command=command,
        diffusion_analysis_id=diffusion_analysis_id,
        migration_hop_id=migration_hop_id,
    )

    # get the supercell endpoint structures
    supercell_start, supercell_end = get_endpoint_structures(
        parameters_cleaned["migration_hop"]
    )

    # Relax the starting supercell structure
    run_id_00 = relax_endpoint(
        structure=supercell_start,
        command=subcommands["command_supercell"],
        directory=parameters_cleaned["directory"]
        + os.path.sep
        + "endpoint_relaxation_start",
    )

    # Relax the ending supercell structure
    run_id_01 = relax_endpoint(
        structure=supercell_end,
        command=subcommands["command_supercell"],
        directory=parameters_cleaned["directory"]
        + os.path.sep
        + "endpoint_relaxation_end",
    )

    images = get_migration_images_from_endpoints(
        supercell_start={
            "calculation_table": "MatVirtualLabCINEBEndpointRelaxation",
            "directory": run_id_00["directory"],
            "structure_field": "structure_final",
        },
        supercell_end={
            "calculation_table": "MatVirtualLabCINEBEndpointRelaxation",
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
        diffusion_analysis_id=diffusion_analysis_id,
        migration_hop_id=migration_hop_id,
    )


workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Diffusion"
# workflow.calculation_table = MITDiffusionAnalysis  # not implemented yet
workflow.result_table = MITDiffusionAnalysis
workflow.s3tasks = [
    relaxation_neb_endpoint_workflow.s3task,
    neb_from_images.s3task,
]

workflow.description_doc_short = "runs NEB using a MigrationHop object as input"
workflow.__doc__ = """
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
