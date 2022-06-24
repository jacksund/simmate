# -*- coding: utf-8 -*-

from simmate.workflow_engine import s3task_to_workflow
from simmate.calculators.vasp.tasks.band_structure import (
    MatProjBandStructure as MatProjBandStructureTask,
)
from simmate.calculators.vasp.database.band_structure import (
    MatProjBandStructure as MatProjBandStructureResults,
)

workflow = s3task_to_workflow(
    name="band-structure/matproj",
    module=__name__,
    project_name="Simmate-Band-Structure",
    s3task=MatProjBandStructureTask,
    database_table=MatProjBandStructureResults,
    register_kwargs=["structure", "source"],
    description_doc_short="uses Materials Project settings (PBE)",
)
