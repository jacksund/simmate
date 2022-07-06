# -*- coding: utf-8 -*-

from simmate.workflow_engine import Workflow
from simmate.calculators.vasp.tasks.population_analysis import (
    MatProjELF as MPPreBaderTask,
)
from simmate.calculators.vasp.database.population_analysis import (
    MatProjELF as MPELFResults,
)


class ELFMatProjPopulationAnalysis(Workflow):
    name = "population-analysis/elf-matproj"
    project_name = "Simmate-PopulationAnalysis"
    s3task = MPPreBaderTask
    database_table = MPELFResults
    register_kwargs = ["structure", "source"]
    description_doc_short = "uses Materials Project settings"
