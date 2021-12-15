# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.quality_04 import (
    Quality04Relaxation as Quality04RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality04Relaxation as Quality04RelaxationResults,
)

workflow = Quality04RelaxationTask.get_workflow(
    name="Quality 04 Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    calculation_table=Quality04RelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
