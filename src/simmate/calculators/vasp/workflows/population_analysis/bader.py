# -*- coding: utf-8 -*-

from simmate.toolkit import Structure
from simmate.workflow_engine import task, Workflow
from simmate.calculators.vasp.tasks.population_analysis import (
    MatprojPreBader as MPPreBaderTask,
)
from simmate.calculators.vasp.database.population_analysis import (
    MatprojBaderAnalysis as MPBaderResults,
)
from simmate.calculators.bader.tasks import (
    BaderAnalysis as BaderAnalysisTask,
    CombineCHGCARs,
)


class PopulationAnalysis__Vasp__BaderMatproj(Workflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density.
    """

    database_table = MPBaderResults

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: str = None,
    ):

        prebader_result = PopulationAnalysis__Vasp__PrebaderMatproj.run(
            structure=structure,
            command=command,
            source=source,
            directory=directory,
        ).result()

        # Setup chargecars for the bader analysis and wait until complete
        CombineCHGCARs.run(directory=prebader_result["directory"]).result()

        # Bader only adds files and doesn't overwrite any, so I just run it
        # in the original directory. I may switch to copying over to a new
        # directory in the future though.
        bader_result = BaderAnalysisTask.run(
            directory=prebader_result["directory"]
        ).result()

        save_bader_results(bader_result, prebader_result["prefect_flow_run_id"])


# -----------------------------------------------------------------------------

# Below are extra tasks and subflows for the workflow that is defined above


class PopulationAnalysis__Vasp__PrebaderMatproj(Workflow):
    s3task = MPPreBaderTask
    database_table = MPBaderResults
    description_doc_short = "uses Materials Project settings with denser FFT grid"


@task
def save_bader_results(bader_result, prefect_flow_run_id):
    # load the results. We are particullary after the first result with
    # is a pandas dataframe of oxidation states.
    oxidation_data, extra_data = bader_result["result"]

    # load the calculation entry for this workflow run. This should already
    # exist thanks to the load_input_and_register task of the prebader workflow
    calculation = MPBaderResults.from_prefect_id(
        prefect_flow_run_id,
    )
    # BUG: can't use context to grab the id because workflow tasks generate a
    # different id than the main workflow

    # now update the calculation entry with our results
    calculation.oxidation_states = list(oxidation_data.oxidation_state.values)
    calculation.save()
