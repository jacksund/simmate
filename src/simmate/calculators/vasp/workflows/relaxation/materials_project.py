# -*- coding: utf-8 -*-

from simmate.workflow_engine.utilities import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MatProjRelaxation as MPRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MatProjRelaxation as MPRelaxationResults,
)

workflow = s3task_to_workflow(
    name="Materials Project Relaxation",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=MPRelaxationTask,
    calculation_table=MPRelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
