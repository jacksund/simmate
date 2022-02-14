# -*- coding: utf-8 -*-

# !!! Should this module be moved to simmate.workflows.common_tasks? There's
# nothing unique to VASP here

import os

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import (
    DistinctPathFinder,
    MigrationHop,
    MigrationImages,
)

from simmate.database.base_data_types.nudged_elastic_band import (
    DiffusionAnalysis as DiffusionAnalysisTable,
    MigrationHop as MigrationHopTable,
    MigrationImage as MigrationImageTable,
)

from simmate.workflow_engine.workflow import Task, task

from typing import List, Tuple


class BuildDiffusionAnalysisTask(Task):
    def __init__(self, diffusion_analyis: DiffusionAnalysisTable, **kwargs):
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

        pathfinder = DistinctPathFinder(
            structure_cleaned,
            migrating_specie,
            **kwargs,
        )
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
            structure=structure_cleaned,
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
        # For now I return the MigrationHop ids -- because this let's me
        # indicate which MigrationHops should be updated later on.
        return hop_ids


@task(nout=2)
def get_endpoint_structures(migration_hop: MigrationHop) -> Tuple[Structure]:
    """
    Simple wrapper for get_sc_structures method that makes it a Prefect task.
    I assume parameters for now
    """
    start_supercell, end_supercell, _ = migration_hop.get_sc_structures(
        vac_mode=True,
    )
    try:
        assert start_supercell != end_supercell
    except:
        raise Exception(
            "This structure has a bug due to a rounding error. "
            "Our team is aware of this bug and it has been fixed for the next "
            "pymatgen-analysis-diffusion release."
        )
    return start_supercell, end_supercell


@task
def get_migration_images_from_endpoints(supercell_start, supercell_end):
    """
    Simple wrapper for from_endpoints method that makes it a Prefect task.
    I assume parameters for now.
    """

    # Make sure we have toolkit objects, and if not, convert them
    supercell_start_cleaned = Structure.from_dynamic(supercell_start)
    supercell_end_cleaned = Structure.from_dynamic(supercell_end)

    images = MigrationImages.from_endpoints(
        structure_start=supercell_start_cleaned,
        structure_end=supercell_end_cleaned,
        nimages=7,  # TODO: have from_endpoints figure out pathway length
    )

    return images


class SaveNEBOutputTask(Task):
    # This is a modification of simmate.workflows.common_tasks.SaveOutputTask

    def __init__(
        self,
        diffusion_analyis_table: DiffusionAnalysisTable,
        migration_hop_table: MigrationHopTable,
        migration_image_table: MigrationImageTable,
        **kwargs,
    ):
        self.diffusion_analyis_table = diffusion_analyis_table
        self.migration_hop_table = migration_hop_table
        self.migration_image_table = migration_image_table
        super().__init__(**kwargs)

    def run(
        self,
        output,
        diffusion_analysis_id: int = None,
        migration_hop_id: int = None,
    ):

        # split our results and corrections (which are given as a dict) into
        # separate variables
        # Our result here is not a VaspRun object, but instead a NEBAnalysis
        # object. See NudgedElasticBandTask.workup()
        result = output["result"]

        # TODO: These aren't saved for now. Consider making MigrationHopTable
        # a Calculation and attaching these there.
        corrections = output["corrections"]
        directory = output["directory"]

        # First, we need a migration_hop database object.
        # All of hops should link to a diffusion_analysis entry, so we check
        # for that here too. The key thing of these statements is that we
        # have a migration_hop_id at the end.

        # If no ids were given, then we make a new entries for each.
        if not diffusion_analysis_id and not migration_hop_id:
            # Note, we have minimal information if this is the case, so these
            # table entries will have a bunch of empty columns.

            # We don't have a bulk structure to use for this class, so we use
            # the first image
            analysis_db = self.diffusion_analyis_table.from_toolkit(
                structure=result.structures[0],
                vacancy_mode=True,  # assume this for now
            )
            analysis_db.save()

            # This table entry will actually be completely empty... It only
            # serves to link the MigrationImages together
            hop_db = self.migration_hop_table(
                diffusion_analysis_id=analysis_db.id,
            )
            hop_db.save()
            migration_hop_id = hop_db.id

        elif diffusion_analysis_id and not migration_hop_id:
            # This table entry will actually be completely empty... It only
            # serves to link the MigrationImages together
            hop_db = self.migration_hop_table(
                diffusion_analysis_id=diffusion_analysis_id
            )
            hop_db.save()
            migration_hop_id = hop_db.id

        elif migration_hop_id:
            # We don't use the hop_id, but making this query ensures it exists.
            hop_db = self.migration_hop_table.objects.get(id=migration_hop_id)
            # Even though it's not required, we make sure the id given for the
            # diffusion analysis table matches this existing hop id.
            if diffusion_analysis_id:
                assert hop_db.diffusion_analysis.id == diffusion_analysis_id

        # Now same migration images and link them to this parent object.
        # Note, the start/end Migration images will exist already in the
        # relaxation database table. We still want to save them again here for
        # easy access.
        for image_number, image_data in enumerate(
            zip(result.structures, result.energies, result.forces, result.r)
        ):
            image, energy, force, distance = image_data
            image_db = self.migration_image_table.from_toolkit(
                structure=image,
                number=image_number,
                force_tangent=force,
                energy=energy,
                structure_distance=distance,
                migration_hop_id=migration_hop_id,
            )
            image_db.save()

        # If the user wants to access results, they can do so through the hop id
        return migration_hop_id
