# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.relaxation import (
    MatVirtualLabCINEBEndpointRelaxation as NEBEndpointRelaxationTask,
)
from simmate.calculators.vasp.database.relaxation import (
    MatVirtualLabCINEBEndpointRelaxation as NEBEndpointRelaxationResults,
)


class Relaxation__VASP__NEB_Endpoint(Workflow):
    s3task = NEBEndpointRelaxationTask
    database_table = NEBEndpointRelaxationResults
    register_kwargs = ["structure", "source"]
    description_doc_short = (
        "uses Materials Project settings and meant for endpoint supercells"
    )
