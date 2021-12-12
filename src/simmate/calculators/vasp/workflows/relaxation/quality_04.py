# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import LoadInputAndRegister, SaveOutputTask
from simmate.calculators.vasp.tasks.relaxation.all import Quality04RelaxationTask
from simmate.database.local_calculations.relaxation import Quality04Relaxation

relax_structure = Quality04RelaxationTask()
load_input_and_register = LoadInputAndRegister(Quality04Relaxation)
save_results = SaveOutputTask(Quality04Relaxation)

with Workflow("Quality 04 Relaxation") as workflow:
    structure = Parameter("structure")
    command = Parameter("command", default="vasp > vasp.out")
    source = Parameter("source", default=None)
    directory = Parameter("directory", default=None)
    use_previous_directory = Parameter("use_previous_directory", default=False)

    structure_pmg, directory_cleaned = load_input_and_register(
        structure,
        source,
        directory,
        use_previous_directory,
    )
    output = relax_structure(
        structure=structure_pmg,
        command=command,
        directory=directory_cleaned,
    )
    calculation_id = save_results(output=output)

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Relaxation"
workflow.calculation_table = Quality04Relaxation
workflow.result_table = Quality04Relaxation
workflow.register_kwargs = ["prefect_flow_run_id", "structure", "source"]
workflow.result_task = output
