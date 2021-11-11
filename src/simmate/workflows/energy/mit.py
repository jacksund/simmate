# -*- coding: utf-8 -*-

from simmate.workflow_engine.prefect import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import load_structure, SaveOutputTask
from simmate.calculators.vasp.tasks.energy.mit import MITStaticEnergyTask
from simmate.database.local_calculations.energy.mit import MITStructure

static_energy = MITStaticEnergyTask()
save_results = SaveOutputTask(MITStructure)

with Workflow("MIT Static Energy") as workflow:
    structure = Parameter("structure")
    vasp_command = Parameter("vasp_command", default="vasp > vasp.out")
    structure_pmg = load_structure(structure)
    output = static_energy(
        structure=structure_pmg,
        command=vasp_command,
    )
    calculation_id = save_results(output=output)

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Energy"
workflow.calculation_table = MITStructure
