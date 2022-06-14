# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import (
    Workflow,
    Parameter,
    ModuleStorage,
    # task,
)
from simmate.workflow_engine.common_tasks import load_input_and_register

from simmate.workflows.static_energy import matproj_workflow as static_workflow
from simmate.workflows.density_of_states import (
    matproj_workflow as dos_workflow,
)
from simmate.workflows.band_structure import matproj_workflow as bs_workflow

static_task = static_workflow.to_workflow_task()
dos_task = dos_workflow.to_workflow_task()
bs_task = bs_workflow.to_workflow_task()

# TODO -- reads results and writes combined dos+bs plot
# @task
# def write_electronic_summary(directory):
#     pass


with Workflow("electronic-structure/matproj") as workflow:

    structure = Parameter("structure")
    command = Parameter("command", default="vasp_std > vasp.out")
    source = Parameter("source", default=None)
    directory = Parameter("directory", default=None)
    copy_previous_directory = Parameter(
        "copy_previous_directory",
        default=False,
    )

    parameters_cleaned = load_input_and_register(
        structure=structure,
        command=command,
        source=source,
        directory=directory,
        copy_previous_directory=copy_previous_directory,
        register_run=False,
    )

    static_result = static_task(
        structure=parameters_cleaned["structure"],
        command=parameters_cleaned["command"],
        directory=parameters_cleaned["directory"] + os.path.sep + "static_energy",
        source=parameters_cleaned["source"],
    )

    dos_result = dos_task(
        structure={
            "calculation_table": static_workflow.result_table.__name__,
            "directory": static_result["directory"],
        },
        command=parameters_cleaned["command"],
        directory=parameters_cleaned["directory"] + os.path.sep + "density_of_states",
        copy_previous_directory=True,
        source=None,  # default to structure dict above
    )

    bs_result = bs_task(
        structure={
            "calculation_table": static_workflow.result_table.__name__,
            "directory": static_result["directory"],
        },
        command=parameters_cleaned["command"],
        directory=parameters_cleaned["directory"] + os.path.sep + "band_structure",
        copy_previous_directory=True,
        source=None,  # default to structure dict above
    )

workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Diffusion"
# workflow.calculation_table = None  # not implemented yet
workflow.result_table = (
    bs_workflow.result_table
)  # not implemented yet. This is a placeholder
workflow.s3tasks = [
    static_workflow.s3task,
    dos_workflow.s3task,
    bs_workflow.s3task,
]

workflow.description_doc_short = "runs DOS and BS at Materials Project settings"
workflow.__doc__ = """
    Runs a static energy calculation followed by non-SCF calculations for
    band structure and density of states.
    
    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - static-energy/matproj
        - band-structure/matproj
        - density-of-states/matproj
        
    Note, these calculations are done using PBE, which is known to underestimate
    band gaps. For higher quality electronic structure calculations, you should
    use HSE instead.
"""
