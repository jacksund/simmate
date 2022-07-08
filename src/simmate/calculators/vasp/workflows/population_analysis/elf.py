# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.population_analysis import (
    MatProjELF as MPPreBaderTask,
)
from simmate.calculators.vasp.database.population_analysis import (
    MatProjELF as MPELFResults,
)


class PopulationAnalysis__Vasp__ElfMatproj(Workflow):
    s3task = MPPreBaderTask
    database_table = MPELFResults
    description_doc_short = "uses Materials Project settings"
