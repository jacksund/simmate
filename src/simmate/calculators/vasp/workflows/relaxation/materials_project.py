# -*- coding: utf-8 -*-

from simmate.workflow_engine.utilities import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation.materials_project import (
    MaterialsProjectRelaxation as MPRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MaterialsProjectRelaxation as MPRelaxationResults,
)

workflow = s3task_to_workflow(
    name="MIT Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=MPRelaxationTask,
    calculation_table=MPRelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
