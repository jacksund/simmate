# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.band_structure import (
    MatprojHSEBandStructure as MatprojBandStructureTask,
)
from simmate.calculators.vasp.database.band_structure import (
    MatprojHSEBandStructure as MatprojBandStructureResults,
)


class ElectronicStructure__Vasp__MatprojBandStructureHse(Workflow):
    s3task = MatprojBandStructureTask
    database_table = MatprojBandStructureResults
    description_doc_short = "uses Materials Project settings (HSE)"
