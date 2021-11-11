# -*- coding: utf-8 -*-

from simmate.workflow_engine.prefect import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import load_input, SaveOutputTask
from simmate.calculators.vasp.tasks.energy.mit import MITStaticEnergyTask
from simmate.database.local_calculations.energy.mit import MITStructure

static_energy = MITStaticEnergyTask()
save_results = SaveOutputTask(MITStructure)

with Workflow("MIT Static Energy") as workflow:
    structure = Parameter("structure")
    command = Parameter("command", default="vasp > vasp.out")
    directory = Parameter("directory", default=None)
    use_previous_directory = Parameter("use_previous_directory", default=False)

    structure_pmg, directory_cleaned = load_input(
        structure,
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
workflow.calculation_table = MITStructure
