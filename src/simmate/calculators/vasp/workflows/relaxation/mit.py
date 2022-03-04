# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MITRelaxation as MITRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MITRelaxation as MITRelaxationResults,
)

workflow = s3task_to_workflow(
    name="relaxation/mit",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=MITRelaxationTask,
    calculation_table=MITRelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
