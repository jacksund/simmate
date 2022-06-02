# -*- coding: utf-8 -*-

from simmate.workflow_engine import (
    s3task_to_workflow,
    task,
    Parameter,
    Workflow,
    ModuleStorage,
)
from simmate.calculators.vasp.tasks.population_analysis import (
    MatProjPreBader as MPPreBaderTask,
)
from simmate.calculators.vasp.database.population_analysis import (
    MatProjBaderAnalysis as MPBaderResults,
)
from simmate.calculators.bader.tasks import BaderAnalysis as BaderAnalysisTask

prebader_workflow = s3task_to_workflow(
    name="population-analysis/prebader-matproj",
    module=__name__,
    project_name="Simmate-PopulationAnalysis",
    s3task=MPPreBaderTask,
    calculation_table=MPBaderResults,
    register_kwargs=["structure", "source"],
    description_doc_short="uses Materials Project settings with denser FFT grid",
)

prebader_task = prebader_workflow.to_workflow_task()


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


bader_task = BaderAnalysisTask()


with Workflow("population-analysis/bader-matproj") as workflow:

    structure = Parameter("structure")
    command = Parameter("command", default="vasp_std > vasp.out")
    source = Parameter("source", default=None)
    directory = Parameter("directory", default=None)

    prebader_result = prebader_task(
        structure=structure,
        command=command,
        source=source,
        directory=directory,
    )

    # Bader only adds files and doesn't overwrite any, so I just run it
    # in the original directory. I may switch to copying over to a new
    # directory in the future though.
    bader_result = bader_task(directory=prebader_result["directory"])

    save_bader_results(bader_result, prebader_result["prefect_flow_run_id"])


workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-PopulationAnalysis"
workflow.calculation_table = MPBaderResults
workflow.result_table = MPBaderResults
workflow.register_kwargs = ["structure", "source"]
workflow.result_task = bader_result
workflow.s3tasks = [MPPreBaderTask, BaderAnalysisTask]

workflow.__doc__ = """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density.
"""
