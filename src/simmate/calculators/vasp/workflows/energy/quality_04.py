# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.energy.quality_04 import (
    Quality04Energy as Quality04EnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    Quality04StaticEnergy as Quality04StaticEnergyResults,
)

workflow = Quality04EnergyTask.get_workflow(
    name="Quality 04 Static Energy",
    module=__name__,
    project_name="Simmate-Energy",
    calculation_table=Quality04StaticEnergyResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
