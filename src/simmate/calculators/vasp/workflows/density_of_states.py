# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.density_of_states import (
    MatProjDensityOfStates as MatProjDensityOfStatesTask,
)
from simmate.calculators.vasp.database.density_of_states import (
    MatProjDensityOfStates as MatProjDensityOfStatesResults,
)

workflow = s3task_to_workflow(
    name="density-of-states/matproj",
    module=__name__,
    project_name="Simmate-Density-of-States",
    s3task=MatProjDensityOfStatesTask,
    database_table=MatProjDensityOfStatesResults,
    register_kwargs=["structure", "source"],
    description_doc_short="uses Materials Project settings (PBE)",
)
