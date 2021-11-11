# -*- coding: utf-8 -*-

from simmate.workflow_engine.prefect import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import load_input, SaveOutputTask
from simmate.calculators.vasp.tasks.relaxation.all import Quality01RelaxationTask
from simmate.database.local_calculations.relaxation.all import Quality01Relaxation

relax_structure = Quality01RelaxationTask()
save_results = SaveOutputTask(Quality01Relaxation)

with Workflow("Quality 01 Relaxation") as workflow:
    structure = Parameter("structure")
    vasp_command = Parameter("vasp_command", default="vasp > vasp.out")
    directory = Parameter("directory", default=None)
    use_previous_directory = Parameter("use_previous_directory", default=False)

    structure_pmg, directory_cleaned = load_input(
        structure,
        directory,
        use_previous_directory,
    )
    output = relax_structure(
        structure=structure_pmg,
        command=vasp_command,
        directory=directory_cleaned,
    )
    calculation_id = save_results(output=output)

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Relaxation"
workflow.calculation_table = Quality01Relaxation
