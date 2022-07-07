# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.band_structure import (
    MatProjBandStructure as MatProjBandStructureTask,
)
from simmate.calculators.vasp.database.band_structure import (
    MatProjBandStructure as MatProjBandStructureResults,
)


class ElectronicStructure__Vasp__MatProjBandStructure(Workflow):
    s3task = MatProjBandStructureTask
    database_table = MatProjBandStructureResults
    register_kwargs = ["structure", "source"]
    description_doc_short = "uses Materials Project settings (PBE)"
