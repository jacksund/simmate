# -*- coding: utf-8 -*-

from simmate.workflow_engine.prefect import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import load_structure, SaveResultTask
from simmate.calculators.vasp.tasks.relaxation.third_party.mit import MITRelaxationTask
from simmate.database.local_calculations.relaxation.mit import MITRelaxation

static_energy = MITRelaxationTask()
save_results = SaveResultTask(MITRelaxation)

with Workflow("MIT Static Energy") as workflow:
    structure = Parameter("structure")
    vasp_command = Parameter("vasp_command", default="vasp > vasp.out")
    structure_pmg = load_structure(structure)
    result = static_energy(
        structure=structure_pmg,
        command=vasp_command,
    )
    calculation_id = save_results(result=result)

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Relaxation"
workflow.calculation_table = MITRelaxation
