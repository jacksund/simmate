# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import LoadInputAndRegister, SaveOutputTask
from simmate.calculators.vasp.tasks.relaxation.third_party.mit import MITRelaxationTask
from simmate.database.local_calculations.relaxation import MITRelaxation

relax_structure = MITRelaxationTask()
load_input_and_register = LoadInputAndRegister(MITRelaxation)
save_results = SaveOutputTask(MITRelaxation)

with Workflow("MIT Relaxation") as workflow:
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
workflow.calculation_table = MITRelaxation
workflow.result_table = MITRelaxation
workflow.register_kwargs = ["prefect_flow_run_id", "structure", "source"]
workflow.result_task = output
