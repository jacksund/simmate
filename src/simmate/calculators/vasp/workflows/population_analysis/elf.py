# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.population_analysis import (
    MatProjELF as MPPreBaderTask,
)
from simmate.calculators.vasp.database.population_analysis import (
    MatProjELF as MPELFResults,
)


workflow = s3task_to_workflow(
    name="population-analysis/elf-matproj",
    module=__name__,
    project_name="Simmate-PopulationAnalysis",
    s3task=MPPreBaderTask,
    calculation_table=MPELFResults,
    register_kwargs=["structure", "source"],
    description_doc_short="uses Materials Project settings",
)
