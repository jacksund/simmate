# -*- coding: utf-8 -*-

# NOTE TO DEVS: This workflow is very close to those made by s3task_to_workflow
# but there are some key differences, which is why we manually make the workflow
# here. Most notably, there is no "structure" parameter here -- instead, this
# flow takes migration_images. The fact that we are passing multiple structures
# changes the naming of some variables in the workflow. For example, we use
# neb_task(structures=...) instead of s3task(structure=...). Further, we also
# accept extra parameters that help link to other tables -- for high-level
# NEB workflows (where many images/hops are linked together). These parameters
# are used in saving the results.

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)
from simmate.workflow_engine.common_tasks import load_input_and_register
from simmate.calculators.vasp.tasks.nudged_elastic_band import MITNudgedElasticBand
from simmate.calculators.vasp.database.nudged_elastic_band import (
    MITDiffusionAnalysis,
    MITMigrationHop,
    MITMigrationImage,
)
from simmate.calculators.vasp.workflows.nudged_elastic_band.utilities import (
    SaveNEBOutputTask,
)

neb_task = MITNudgedElasticBand()
save_results = SaveNEBOutputTask(
    MITDiffusionAnalysis,
    MITMigrationHop,
    MITMigrationImage,
)

with Workflow("diffusion/from-images") as workflow:

    migration_images = Parameter("migration_images")
    command = Parameter("command", default="vasp_std > vasp.out")
    source = Parameter("source", default=None)
    directory = Parameter("directory", default=None)
    # assume copy_previous_directory=False for now

    # These parameters link to higher-level tables.
    diffusion_analysis_id = Parameter("diffusion_analysis_id", default=None)
    migration_hop_id = Parameter("migration_hop_id", default=None)

    # Load our input and make a base directory for all other workflows to run
    # within for us.
    parameters_cleaned = load_input_and_register(
        migration_images=migration_images,
        source=source,
        directory=directory,
        command=command,
        register_run=False,  # temporary fix bc no calc table exists yet
    )

    output = neb_task(
        structures=parameters_cleaned["migration_images"],
        command=parameters_cleaned["command"],
        directory=parameters_cleaned["directory"],
    )

    calculation_id = save_results(
        output=output,
        diffusion_analysis_id=diffusion_analysis_id,
        migration_hop_id=migration_hop_id,
    )  # calculation_id will correspond to the migration hop table


workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Diffusion"
workflow.database_table = MITMigrationImage
workflow.result_task = output
workflow.s3task = neb_task

workflow.description_doc_short = "runs NEB using a series of structures images as input"
workflow.__doc__ = """
    Runs a NEB relaxation on a list of structures (aka images) using MIT Project
    settings. The lattice remains fixed and symmetry is turned off for this
    relaxation.
    
    Typically, this workflow is not ran directly -- but instead, you would
    use diffusion/all-paths which submits a series of this workflow for you. Other
    higher level workflows that call this one include diffusion/from-endpoints
    and diffusion/single-path.
"""
