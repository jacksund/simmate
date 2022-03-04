# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality04Relaxation as Quality04RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality04Relaxation as Quality04RelaxationResults,
)

workflow = s3task_to_workflow(
    name="relaxation/quality04",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=Quality04RelaxationTask,
    calculation_table=Quality04RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
