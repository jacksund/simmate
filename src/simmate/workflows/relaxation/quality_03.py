# -*- coding: utf-8 -*-

from simmate.workflow_engine.prefect import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import load_input, SaveOutputTask
from simmate.calculators.vasp.tasks.relaxation.all import Quality03RelaxationTask
from simmate.database.local_calculations.relaxation.all import Quality03Relaxation

static_energy = Quality03RelaxationTask()
save_results = SaveOutputTask(Quality03Relaxation)

with Workflow("Quality 03 Relaxation") as workflow:
    structure = Parameter("structure")
    vasp_command = Parameter("vasp_command", default="vasp > vasp.out")
    structure_pmg = load_input(structure)
    output = static_energy(
        structure=structure_pmg,
        command=vasp_command,
    )
    calculation_id = save_results(output=output)

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Relaxation"
workflow.calculation_table = Quality03Relaxation
