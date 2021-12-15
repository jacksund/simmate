# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.quality_03 import (
    Quality03Relaxation as Quality03RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality03Relaxation as Quality03RelaxationResults,
)

workflow = Quality03RelaxationTask.get_workflow(
    name="Quality 03 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    calculation_table=Quality03RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
