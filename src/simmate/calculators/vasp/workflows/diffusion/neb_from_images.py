# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow, task
from simmate.workflow_engine.common_tasks import load_input_and_register
from simmate.calculators.vasp.tasks.nudged_elastic_band import (
    MITNudgedElasticBand,
)
from simmate.calculators.vasp.database.nudged_elastic_band import (
    # MITDiffusionAnalysis,
    MITMigrationHop,
    MITMigrationImage,
)
from simmate.database.base_data_types.nudged_elastic_band import (
    # DiffusionAnalysis as DiffusionAnalysisTable,
    MigrationHop as MigrationHopTable,
    MigrationImage as MigrationImageTable,
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
        is_restart: bool = False,
    ):

        # Load our input and make a base directory for all other workflows to run
        # within for us.
        parameters_cleaned = load_input_and_register(
            migration_images=migration_images,
            source=source,
            directory=directory,
            command=command,
            is_restart=is_restart,
            register_run=False,  # temporary fix bc no calc table exists yet
        ).result()

        result = cls.s3task.run(**parameters_cleaned).result()

        calculation_id = save_neb_results(
            output=result,
            # migration_hop_table=MITDiffusionAnalysis,
            migration_hop_table=MITMigrationHop,
            migration_image_table=MITMigrationImage,
            diffusion_analysis_id=diffusion_analysis_id,
            migration_hop_id=migration_hop_id,
        )  # calculation_id will correspond to the migration hop table

        return result


@task
def save_neb_results(
    output,
    # diffusion_analyis_table: DiffusionAnalysisTable,
    migration_hop_table: MigrationHopTable,
    migration_image_table: MigrationImageTable,
    diffusion_analysis_id: int = None,
    migration_hop_id: int = None,
):

    # split our results and corrections (which are given as a dict) into
    # separate variables
    # Our result here is not a VaspRun object, but instead a NEBAnalysis
    # object. See NudgedElasticBandTask.workup()
    result = output["result"]

    # TODO: These aren't saved for now. Consider making MigrationHopTable
    # a Calculation and attaching these there.
    corrections = output["corrections"]
    directory = output["directory"]

    # First, we need a migration_hop database object.
    # All of hops should link to a diffusion_analysis entry, so we check
    # for that here too. The key thing of these statements is that we
    # have a migration_hop_id at the end.

    migration_hop_db = migration_hop_table.from_pymatgen(
        analysis=result,
        diffusion_analysis_id=diffusion_analysis_id,
        migration_hop_id=migration_hop_id,
    )

    # If the user wants to access results, they can do so through the hop id
    return migration_hop_db.id
