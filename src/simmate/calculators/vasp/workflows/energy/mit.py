# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.energy.mit import (
    MITStaticEnergy as MITStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    MITStaticEnergy as MITStaticEnergyResults,
)

workflow = MITStaticEnergyTask.get_workflow(
    name="MIT Static Energy",
    module=__name__,
    project_name="Simmate-Energy",
    calculation_table=MITStaticEnergyResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
