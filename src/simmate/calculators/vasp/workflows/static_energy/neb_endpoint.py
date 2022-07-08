# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.static_energy import (
    NEBEndpointStaticEnergy as NEBEndpointStaticEnergyTask,
)
from simmate.calculators.vasp.database.energy import (
    NEBEndpointStaticEnergy as NEBEndpointStaticEnergyResults,
)


class StaticEnergy__Vasp__NebEndpoint(Workflow):
    s3task = NEBEndpointStaticEnergyTask
    database_table = NEBEndpointStaticEnergyResults
    description_doc_short = (
        "uses Materials Project settings meant for defect supercell structures"
    )
