# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import LoadInputAndRegister, SaveOutputTask
from simmate.calculators.vasp.tasks.relaxation.all import Quality03RelaxationTask
from simmate.database.local_calculations.relaxation import Quality03Relaxation

relax_structure = Quality03RelaxationTask()
load_input_and_register = LoadInputAndRegister(Quality03Relaxation)
save_results = SaveOutputTask(Quality03Relaxation)

with Workflow("Quality 03 Relaxation") as workflow:
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
workflow.calculation_table = Quality03Relaxation
workflow.result_table = Quality03Relaxation
workflow.register_kwargs = ["prefect_flow_run_id", "structure", "source"]
workflow.result_task = output
