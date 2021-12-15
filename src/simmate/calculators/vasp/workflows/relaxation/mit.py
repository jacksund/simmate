# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.mit import (
    MITRelaxation as MITRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MITRelaxation as MITRelaxationResults,
)

workflow = MITRelaxationTask.get_workflow(
    name="MIT Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    calculation_table=MITRelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
