# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.energy import (
    Quality04Energy as Quality04EnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    Quality04StaticEnergy as Quality04StaticEnergyResults,
)

workflow = s3task_to_workflow(
    name="static-energy/quality04",
    module=__name__,
    project_name="Simmate-Energy",
    s3task=Quality04EnergyTask,
    calculation_table=Quality04StaticEnergyResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
