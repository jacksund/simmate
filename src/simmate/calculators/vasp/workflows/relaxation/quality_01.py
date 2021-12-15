# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.quality_01 import (
    Quality01Relaxation as Quality01RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality01Relaxation as Quality01RelaxationResults,
)

workflow = Quality01RelaxationTask.get_workflow(
    name="Quality 01 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    calculation_table=Quality01RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
