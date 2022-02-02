# -*- coding: utf-8 -*-

# !!! Should this module be moved to simmate.workflows.common_tasks? There's
# nothing unique to VASP here

import os

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import DistinctPathFinder, MigrationHop

from simmate.database.base_data_types import DiffusionAnalysis

from simmate.workflow_engine.workflow import Task

from typing import List


class BuildDiffusionAnalysisTask(Task):
    def __init__(self, diffusion_analyis: DiffusionAnalysis, **kwargs):
        self.diffusion_analyis = diffusion_analyis
        super().__init__(**kwargs)

    def run(
        self,
        structure: Structure,
        migrating_specie: str,
        vacancy_mode: bool,
        directory: str = "",
        **kwargs,
    ) -> List[MigrationHop]:
        """
        Given a bulk crystal structure, returns all symmetrically unique pathways
        for the migrating specie (up until the path is percolating). This
        also create all relevent database entries for this struture and its
        migration hops.

        Parameters
        ----------

        - `structure`:
            bulk crystal structure to be analyzed. Can be in any format supported
            by Structure.from_dynamic method.

        - `migrating_specie`:
            Element or ion symbol of the diffusion specie (e.g. "Li")

        - `directory`:
            where to write the CIF file visualizing all migration hops. If no
            directory is provided, it will be written in the working directory.

        - `**kwargs`:
            Any parameter normally accepted by DistinctPathFinder
        """

        ###### STEP 1: creating the toolkit objects and writing them to file

        structure_cleaned = Structure.from_dynamic(structure)

        pathfinder = DistinctPathFinder(structure_cleaned, migrating_specie, **kwargs)
        migration_hops = pathfinder.get_paths()

        # We write all the path files so users can visualized them if needed
        filename = os.path.join(directory, "migration_hop_all.cif")
        pathfinder.write_all_paths(filename, nimages=10)
        for i, migration_hop in enumerate(migration_hops):
            number = str(i).zfill(2)  # converts numbers like 2 to "02"
            # the files names here will be like "migration_hop_02.cif"
            migration_hop.write_path(
                os.path.join(directory, f"migration_hop_{number}.cif"),
                nimages=10,
            )

        ###### STEP 2: creating the database objects and saving them to the db

        # Create the main DiffusionAnalysis object that others will link to.
        da_obj = self.diffusion_analyis.from_toolkit(
            structure=structure,
            migrating_specie=migrating_specie,
            vacancy_mode=vacancy_mode,
        )
        da_obj.save()
        # TODO: should I search for a matching bulk structure before deciding
        # to create a new DiffusionAnalysis entry?

        # grab the linked MigrationHop class
        hop_class = da_obj.migration_hops.model

        # Now iterate through the hops and add them to the database
        hop_ids = []
        for i, hop in enumerate(migration_hops):
            hop_db = hop_class.from_toolkit(
                migration_hop=hop,
                number=i,
                diffusion_analysis_id=da_obj.id,
            )
            hop_db.save()
            hop_ids.append(hop_db.id)

        # TODO: still figuring out if toolkit vs. db objects should be returned.
        # Maybe add ids to the toolkit objects? Or dynamic DB dictionaries?
        #
        # Once this is all done, return the Migration hop ____ entries.
        # We do this instead of the ____ objects because ...
        return hop_ids
