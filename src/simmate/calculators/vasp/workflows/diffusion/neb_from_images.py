# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import Workflow
from simmate.workflow_engine.common_tasks import load_input_and_register
from simmate.calculators.vasp.tasks.nudged_elastic_band import (
    MITNudgedElasticBand,
)
from simmate.calculators.vasp.database.nudged_elastic_band import (
    MITDiffusionAnalysis,
    MITMigrationHop,
    MITMigrationImage,
)
from simmate.calculators.vasp.workflows.nudged_elastic_band.utilities import (
    SaveNEBOutputTask,
)


class Diffusion__Vasp__NebFromImages(Workflow):
    """
    Runs a NEB relaxation on a list of structures (aka images) using MIT Project
    settings. The lattice remains fixed and symmetry is turned off for this
    relaxation.

    Typically, this workflow is not ran directly -- but instead, you would
    use diffusion/all-paths which submits a series of this workflow for you. Other
    higher level workflows that call this one include diffusion/from-endpoints
    and diffusion/single-path.
    """

    database_table = MITMigrationImage
    s3task = MITNudgedElasticBand
    description_doc_short = "runs NEB using a series of structures images as input"

    @classmethod
    def run_config(
        cls,
        migration_images,
        command: str = None,
        source: dict = None,
        directory: str = None,
        # These help link results to a higher-level table.
        diffusion_analysis_id: int = None,
        migration_hop_id: int = None,
        # TODO: Can the hop id be inferred from the migration_hop or somewhere
        # else in this context? Maybe even load_input_and_register will use
        # prefect id once it's a Calculation?
    ):

        # Load our input and make a base directory for all other workflows to run
        # within for us.
        parameters_cleaned = load_input_and_register(
            migration_images=migration_images,
            source=source,
            directory=directory,
            command=command,
            register_run=False,  # temporary fix bc no calc table exists yet
        )

        result = cls.s3task.run(**parameters_cleaned).result()

        save_results_task = SaveNEBOutputTask(
            MITDiffusionAnalysis,
            MITMigrationHop,
            MITMigrationImage,
        )
        calculation_id = save_results_task(
            output=result,
            diffusion_analysis_id=diffusion_analysis_id,
            migration_hop_id=migration_hop_id,
        )  # calculation_id will correspond to the migration hop table

        return result
