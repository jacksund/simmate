# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    NEBEndpointStaticEnergy as NEBEndpointStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    NEBEndpointStaticEnergy as NEBEndpointStaticEnergyResults,
)


class NEBEndpointStaticEnergy(Workflow):
    name = "static-energy/neb-endpoint"
    project_name = "Simmate-Energy"
    s3task = NEBEndpointStaticEnergyTask
    database_table = NEBEndpointStaticEnergyResults
    register_kwargs = ["structure", "source"]
    description_doc_short = (
        "uses Materials Project settings meant for defect supercell structures"
    )
