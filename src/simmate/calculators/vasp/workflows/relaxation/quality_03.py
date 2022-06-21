# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.relaxation import (
    Quality03Relaxation as Quality03RelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    Quality03Relaxation as Quality03RelaxationResults,
)

workflow = s3task_to_workflow(
    name="relaxation/quality03",
    module=__name__,
    project_name="Simmate-Relaxation",
    s3task=Quality03RelaxationTask,
    database_table=Quality03RelaxationResults,
    register_kwargs=["structure", "source"],
    description_doc_short="low-quality settings meant for highly unreasonable structures",
)
