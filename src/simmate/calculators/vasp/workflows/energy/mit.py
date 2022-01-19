# -*- coding: utf-8 -*-

from simmate.workflow_engine.utilities import s3task_to_workflow
from simmate.calculators.vasp.tasks.energy import (
    MITStaticEnergy as MITStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    MITStaticEnergy as MITStaticEnergyResults,
)

workflow = s3task_to_workflow(
    name="MIT Static Energy",
    module=__name__,
    project_name="Simmate-Energy",
    s3task=MITStaticEnergyTask,
    calculation_table=MITStaticEnergyResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
