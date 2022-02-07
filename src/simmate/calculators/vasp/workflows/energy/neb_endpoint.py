# -*- coding: utf-8 -*-

from simmate.workflow_engine.utilities import s3task_to_workflow
from simmate.calculators.vasp.tasks.energy import (
    NEBEndpointStaticEnergy as NEBEndpointStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    NEBEndpointStaticEnergy as NEBEndpointStaticEnergyResults,
)

workflow = s3task_to_workflow(
    name="NEB Endpoint Static Energy",
    module=__name__,
    project_name="Simmate-Energy",
    s3task=NEBEndpointStaticEnergyTask,
    calculation_table=NEBEndpointStaticEnergyResults,
    register_kwargs=["prefect_flow_run_id", "structure", "source"],
)
