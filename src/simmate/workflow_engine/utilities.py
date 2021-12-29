# -*- coding: utf-8 -*-

from simmate.workflow_engine.workflow import (
    Workflow,
    Parameter,
    ModuleStorage,
)
from simmate.workflows.common_tasks.all import (
    LoadInputAndRegister,
    SaveOutputTask,
)

from typing import List
from simmate.workflow_engine.tasks.supervised_staged_shell_task import (
    SupervisedStagedShellTask,
)


def s3task_to_workflow(
    name: str,
    module: str,
    project_name: str,
    s3task: SupervisedStagedShellTask,
    calculation_table,  # simmate.database.base_data_types.calculation.Calculation
    register_kwargs: List[str],
):
    """
    Builds a workflow from a S3Task and it's corresponding database table.

    Very often with Simmate's S3Tasks, the workflow for a single S3Task is
    the same. The workflow is typically made of three tasks:
        (1) loading the input parameters and registering the calculation
        (2) running the calculation (what this S3Task does on its own)
        (3) saving the calculation results
    Task 1 and 3 always use the same functions, where we just need to tell
    it which database table we are registering/saving to.

    Because of this common recipe for workflows, we use this method to make
    the workflow for us.
    """

    s3task_obj = s3task()  # Use defaults
    load_input_and_register = LoadInputAndRegister(calculation_table)
    save_results = SaveOutputTask(calculation_table)

    with Workflow(name) as workflow:
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
        output = s3task_obj(
            structure=structure_pmg,
            command=command,
            directory=directory_cleaned,
        )
        calculation_id = save_results(output=output)

    workflow.storage = ModuleStorage(module)
    workflow.project_name = project_name
    workflow.calculation_table = calculation_table
    workflow.result_table = calculation_table
    workflow.register_kwargs = register_kwargs
    workflow.result_task = output
    workflow.s3task = s3task

    return workflow
