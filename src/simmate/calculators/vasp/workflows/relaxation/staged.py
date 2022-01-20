# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)

from simmate.calculators.vasp.workflows.relaxation.quality_00 import (
    workflow as relaxation_quality00,
)
from simmate.calculators.vasp.workflows.relaxation.quality_01 import (
    workflow as relaxation_quality01,
)
from simmate.calculators.vasp.workflows.relaxation.quality_02 import (
    workflow as relaxation_quality02,
)
from simmate.calculators.vasp.workflows.relaxation.quality_03 import (
    workflow as relaxation_quality03,
)
from simmate.calculators.vasp.workflows.relaxation.quality_04 import (
    workflow as relaxation_quality04,
)
from simmate.calculators.vasp.workflows.energy.quality_04 import (
    workflow as energy_quality04,
)

from simmate.calculators.vasp.database.relaxation import StagedRelaxation
from simmate.calculators.vasp.database.energy import Quality04StaticEnergy


# init workflow tasks
# OPTIMIZE: Make this a for-loop in Prefect 2.0! We can use a for-loop in the
# workflow context below too.
relax_task_00 = relaxation_quality00.to_workflow_task()
relax_task_01 = relaxation_quality01.to_workflow_task()
relax_task_02 = relaxation_quality02.to_workflow_task()
relax_task_03 = relaxation_quality03.to_workflow_task()
relax_task_04 = relaxation_quality04.to_workflow_task()
static_task_04 = energy_quality04.to_workflow_task()

with Workflow("Staged Relaxation") as workflow:

    structure = Parameter("structure")
    command = Parameter("command", default="vasp_std > vasp.out")

    # Our first relaxation is directly from our inputs. The remaining one
    # pass along results
    run_id_00 = relax_task_00(
        structure=structure,
        command=command,
    )

    # TODO: Use a for-loop in Prefect 2.0!

    # relaxation 01
    run_id_01 = relax_task_01(
        structure={
            "calculation_table": "Quality00Relaxation",
            "directory": run_id_00["directory"],
            "structure_field": "structure_final",
        },
        command=command,
    )

    # relaxation 02
    run_id_02 = relax_task_02(
        structure={
            "calculation_table": "Quality01Relaxation",
            "directory": run_id_01["directory"],
            "structure_field": "structure_final",
        },
        command=command,
    )

    # relaxation 03
    run_id_03 = relax_task_03(
        structure={
            "calculation_table": "Quality02Relaxation",
            "directory": run_id_02["directory"],
            "structure_field": "structure_final",
        },
        command=command,
    )

    # relaxation 04
    run_id_04 = relax_task_04(
        structure={
            "calculation_table": "Quality03Relaxation",
            "directory": run_id_03["directory"],
            "structure_field": "structure_final",
        },
        command=command,
    )

    # Static Energy (same quality as 04 relaxation)
    run_id_05 = static_task_04(
        structure={
            "calculation_table": "Quality04Relaxation",
            "directory": run_id_04["directory"],
            "structure_field": "structure_final",
        },
        command=command,
    )

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Relaxation"
workflow.calculation_table = StagedRelaxation
workflow.result_table = Quality04StaticEnergy
workflow.register_kwargs = ["prefect_flow_run_id"]
workflow.result_task = run_id_05
workflow.s3tasks = [
    w.s3task
    for w in [
        relaxation_quality00,
        relaxation_quality01,
        relaxation_quality02,
        relaxation_quality03,
        relaxation_quality04,
        energy_quality04,
    ]
]

workflow.__doc__ = """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.
    
    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - relaxation/quality00
        - relaxation/quality01
        - relaxation/quality02
        - relaxation/quality03
        - relaxation/quality04
        - static-energy/quality04
    
    This workflow is most useful for randomly-created structures or extremely 
    large supercells. More precise relaxations+energy calcs should be done 
    afterwards because ettings are still below MIT and Materials Project quality.
"""
