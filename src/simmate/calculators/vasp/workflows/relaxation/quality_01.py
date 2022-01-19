# -*- coding: utf-8 -*-

from simmate.workflow_engine.utilities import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality01Relaxation as Quality01RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality01Relaxation as Quality01RelaxationResults,
)

workflow = s3task_to_workflow(
    name="Quality 01 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=Quality01RelaxationTask,
    calculation_table=Quality01RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
