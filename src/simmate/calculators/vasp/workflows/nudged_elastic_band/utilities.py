# -*- coding: utf-8 -*-

# !!! Should this module be moved to simmate.workflows.common_tasks? There's
# nothing unique to VASP here

import os

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import DistinctPathFinder, MigrationHop

from simmate.database.base_data_types import DiffusionAnalysis

from simmate.workflow_engine.workflow import task, Task

from typing import List


@task
def get_migration_hops(
    structure: Structure,
    migrating_specie: str,
    directory: str = "",
    **kwargs,
) -> List[MigrationHop]:
    """
    Given a bulk crystal structure, returns all symmetrically unique pathways
    for the migrating specie (up until the path is percolating).

    This is effectively a wrapper around DistinctPathFinder that converts it
    to a prefect task.

    Parameters
    ----------

    - `structure`:
        bulk crystal structure to be analyzed

    - `migrating_specie`:
        Element or ion symbol of the diffusion specie (e.g. "Li")

    - `directory`:
        where to write the CIF file visualizing all migration hops. If no
        directory is provided, it will be written in the working directory.
    """
    pathfinder = DistinctPathFinder(structure, migrating_specie, **kwargs)
    all_hops = pathfinder.get_paths()

    filename = os.path.join(directory, "all_migration_hops.cif")
    pathfinder.write_all_paths(filename, nimages=10)

    return all_hops


class BuildDiffusionAnalysisTask(Task):
    def __init__(self, diffusion_analyis: DiffusionAnalysis, **kwargs):
        self.diffusion_analyis = diffusion_analyis
        super().__init__(**kwargs)

    def run(
        self,
        structure: Structure,
        vacancy_mode: bool,
        migration_hops: List[MigrationHop],
    ):

        # TODO: should I search for a matching bulk structure before deciding
        # to create a new DiffusionAnalysis entry

        # Create the main DiffusionAnalysis object that others will link to.
        diff_anal = self.diffusion_analyis.from_toolkit(
            structure=structure,
            vacancy_mode=vacancy_mode,
        )
        diff_anal.save()
