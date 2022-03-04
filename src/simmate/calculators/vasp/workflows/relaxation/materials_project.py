# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MatProjRelaxation as MPRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MatProjRelaxation as MPRelaxationResults,
)

workflow = s3task_to_workflow(
    name="relaxation/matproj",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=MPRelaxationTask,
    calculation_table=MPRelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
