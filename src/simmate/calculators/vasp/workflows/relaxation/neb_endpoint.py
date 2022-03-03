# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    NEBEndpointRelaxation as NEBEndpointRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    NEBEndpointRelaxation as NEBEndpointRelaxationResults,
)

workflow = s3task_to_workflow(
    name="relaxation/neb-endpoint",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=NEBEndpointRelaxationTask,
    calculation_table=NEBEndpointRelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
