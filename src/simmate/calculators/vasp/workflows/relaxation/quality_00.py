# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.quality_00 import (
    Quality00Relaxation as Quality00RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality00Relaxation as Quality00RelaxationResults,
)

workflow = Quality00RelaxationTask.get_workflow(
    name="Quality 00 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    calculation_table=Quality00RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
