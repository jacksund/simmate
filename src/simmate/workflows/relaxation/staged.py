# -*- coding: utf-8 -*-

"""
I really don't like how this code looks. If I can get prefect to implement a 
few extra features this will be MUCH better though. Specifically...
    allow accessing of task result attributes 
        --> see bug discussion in vasptask base
    a way to grab results from a Prefect workflow runs 
        --> so that I can have this as a workflow of workflows
"""


from simmate.workflow_engine.prefect import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.workflows.common_tasks.all import load_input, SaveOutputTask
from simmate.calculators.vasp.tasks.relaxation.all import (
    Quality00RelaxationTask,
    Quality01RelaxationTask,
    Quality02RelaxationTask,
    Quality03RelaxationTask,
    Quality04RelaxationTask,
)
from simmate.database.local_calculations.relaxation.all import (
    Quality00Relaxation,
    Quality01Relaxation,
    Quality02Relaxation,
    Quality03Relaxation,
    Quality04Relaxation,
)
from simmate.calculators.vasp.tasks.energy.mit import MITStaticEnergyTask
from simmate.database.local_calculations.energy.mit import MITStructure

relax_structure_00 = Quality00RelaxationTask()
save_results_00 = SaveOutputTask(Quality00Relaxation)

relax_structure_01 = Quality01RelaxationTask()
save_results_01 = SaveOutputTask(Quality01Relaxation)

relax_structure_02 = Quality02RelaxationTask()
save_results_02 = SaveOutputTask(Quality02Relaxation)

relax_structure_03 = Quality03RelaxationTask()
save_results_03 = SaveOutputTask(Quality03Relaxation)

relax_structure_04 = Quality04RelaxationTask()
save_results_04 = SaveOutputTask(Quality04Relaxation)

static_energy = MITStaticEnergyTask()
save_results = SaveOutputTask(MITStructure)

# BUG-FIX: see vasptask base for more
relax_structure_00.return_final_structure = True
relax_structure_01.return_final_structure = True
relax_structure_02.return_final_structure = True
relax_structure_03.return_final_structure = True
relax_structure_04.return_final_structure = True

with Workflow("Staged Relaxation") as workflow:
    structure = Parameter("structure")
    vasp_command = Parameter("vasp_command", default="vasp > vasp.out")
    structure_pmg = load_input(structure)

    # relaxation 00
    output_00 = relax_structure_00(
        structure=structure_pmg,
        command=vasp_command,
    )
    calculation_id_00 = save_results_00(output=output_00)

    # relaxation 01
    output_01 = relax_structure_01(
        structure=output_00["result"]["structure_final"],
        command=vasp_command,
        directory=output_00["directory"],  # uses same directory as before
    )
    calculation_id_01 = save_results_01(output=output_01)

    # relaxation 02
    output_02 = relax_structure_02(
        structure=output_01["result"]["structure_final"],
        command=vasp_command,
        directory=output_01["directory"],  # uses same directory as before
    )
    calculation_id_02 = save_results_02(output=output_02)

    # relaxation 03
    output_03 = relax_structure_03(
        structure=output_02["result"]["structure_final"],
        command=vasp_command,
        directory=output_02["directory"],  # uses same directory as before
    )
    calculation_id_03 = save_results_03(output=output_03)

    # relaxation 04
    output_04 = relax_structure_04(
        structure=output_03["result"]["structure_final"],
        command=vasp_command,
        directory=output_03["directory"],  # uses same directory as before
    )
    calculation_id_04 = save_results_04(output=output_04)

    # final static energy
    output_static = static_energy(
        structure=output_04["result"]["structure_final"],
        command=vasp_command,
        directory=output_04["directory"],  # uses same directory as before
    )
    calculation_id_static = save_results(output=output_static)

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Relaxation"
workflow.calculation_table = MITStructure
