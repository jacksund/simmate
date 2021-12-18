# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.quality_02 import (
    Quality02Relaxation as Quality02RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality02Relaxation as Quality02RelaxationResults,
)

workflow = Quality02RelaxationTask.get_workflow(
    name="Quality 02 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    calculation_table=Quality02RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
