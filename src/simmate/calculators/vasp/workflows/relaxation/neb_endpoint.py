# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MatVirtualLabCINEBEndpointRelaxation as NEBEndpointRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MatVirtualLabCINEBEndpointRelaxation as NEBEndpointRelaxationResults,
)

workflow = s3task_to_workflow(
    name="relaxation/neb-endpoint",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=NEBEndpointRelaxationTask,
    calculation_table=NEBEndpointRelaxationResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
    description_doc_short="uses Materials Project settings and meant for endpoint supercells",
)
