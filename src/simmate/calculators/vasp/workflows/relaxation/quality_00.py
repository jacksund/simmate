# -*- coding: utf-8 -*-

from simmate.workflow_engine.utilities import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality00Relaxation as Quality00RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality00Relaxation as Quality00RelaxationResults,
)

workflow = s3task_to_workflow(
    name="Quality 00 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=Quality00RelaxationTask,
    calculation_table=Quality00RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
