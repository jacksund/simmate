# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality02Relaxation as Quality02RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality02Relaxation as Quality02RelaxationResults,
)

workflow = s3task_to_workflow(
    name="relaxation/quality02",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=Quality02RelaxationTask,
    database_table=Quality02RelaxationResults,
    register_kwargs=["structure", "source"],
    description_doc_short="low-quality settings meant for highly unreasonable structures",
)
