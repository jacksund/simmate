# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import LoadInputAndRegister, SaveOutputTask
from simmate.calculators.vasp.tasks.energy.mit import MITStaticEnergyTask
from simmate.database.local_calculations.energy import MITStaticEnergy

static_energy = MITStaticEnergyTask()
load_input_and_register = LoadInputAndRegister(MITStaticEnergy)
save_results = SaveOutputTask(MITStaticEnergy)

with Workflow("MIT Static Energy") as workflow:
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
    output = static_energy(
        structure=structure_pmg,
        command=command,
        directory=directory_cleaned,
    )
    calculation_id = save_results(output=output)

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Energy"
workflow.calculation_table = MITStaticEnergy
workflow.result_table = MITStaticEnergy
workflow.register_kwargs = ["prefect_flow_run_id", "structure", "source"]
workflow.result_task = output
