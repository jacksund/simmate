# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import LoadInputAndRegister, SaveOutputTask
from simmate.calculators.vasp.tasks.energy.quality_04 import Quality04EnergyTask
from simmate.database.local_calculations.energy import Quality04StaticEnergy

static_energy = Quality04EnergyTask()
load_input_and_register = LoadInputAndRegister(Quality04StaticEnergy)
save_results = SaveOutputTask(Quality04StaticEnergy)

with Workflow("Quality 04 Static Energy") as workflow:
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
workflow.calculation_table = Quality04StaticEnergy
workflow.result_table = Quality04StaticEnergy
workflow.register_kwargs = ["prefect_flow_run_id", "structure", "source"]
workflow.result_task = output
