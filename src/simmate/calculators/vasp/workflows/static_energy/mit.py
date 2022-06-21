# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.static_energy import (
    MITStaticEnergy as MITStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    MITStaticEnergy as MITStaticEnergyResults,
)

workflow = s3task_to_workflow(
    name="static-energy/mit",
    module=__name__,
    project_name="Simmate-Energy",
    s3task=MITStaticEnergyTask,
    database_table=MITStaticEnergyResults,
    register_kwargs=["structure", "source"],
    description_doc_short="uses MIT Project settings",
)
