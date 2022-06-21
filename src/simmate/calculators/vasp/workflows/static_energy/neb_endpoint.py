# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.static_energy import (
    NEBEndpointStaticEnergy as NEBEndpointStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    NEBEndpointStaticEnergy as NEBEndpointStaticEnergyResults,
)

workflow = s3task_to_workflow(
    name="static-energy/neb-endpoint",
    module=__name__,
    project_name="Simmate-Energy",
    s3task=NEBEndpointStaticEnergyTask,
    database_table=NEBEndpointStaticEnergyResults,
    register_kwargs=["structure", "source"],
    description_doc_short="uses Materials Project settings meant for defect supercell structures",
)
