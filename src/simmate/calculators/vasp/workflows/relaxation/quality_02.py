# -*- coding: utf-8 -*-

from simmate.workflow_engine.utilities import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality02Relaxation as Quality02RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality02Relaxation as Quality02RelaxationResults,
)

workflow = s3task_to_workflow(
    name="Quality 02 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=Quality02RelaxationTask,
    calculation_table=Quality02RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
