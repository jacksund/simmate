# -*- coding: utf-8 -*-

import logging
import shutil
from pathlib import Path

from simmate.apps.evolution.models.fixed_composition import FixedCompositionSearch
from simmate.engine import Workflow


class StructurePrediction__Toolkit__NewIndividual(Workflow):
    """
    Generates a new individual for an evolutionary search algorithm.

    Note, this workflow should not be called directly, but instead used within
    higher level workflows (such as `fixed-composition`).

    Users will rarely (if ever) need to call this workflow
    """

    description_doc_short = "a single structure submission for a search"

    has_prerequisite = True
    use_database = False

    @staticmethod
    def run_config(
        search_id: int,
        steadystate_source_id: int,
        directory: Path,
        **kwargs,
    ):
        search_db = FixedCompositionSearch.objects.get(id=search_id)
        source_db = search_db.steadystate_sources.get(id=steadystate_source_id)
        validator = search_db.validator

        # Check the stop condition of the search and see if this new individual
        # is even needed. This will catch when a search ends while a new
        # individual was waiting in the queue
        if search_db.check_stop_condition():
            logging.info(
                "The search ended while this individual was in the queue. "
                "Canceling new individual."
            )
            shutil.rmtree(directory)
            return

        if source_db.is_transformation:
            transformer = source_db.to_toolkit()

            # Check the cache first to save time (even though it might be outdated)
            # and then actually calculate all unique as a backup
            # We only activate the caching once we have >200 unique structures,
            # as that is when it starts to cut into CPU time.
            use_cache = bool(len(search_db.unique_individuals_ids) >= 400)
            unique_queryset = search_db.get_unique_individuals(
                use_cache=use_cache,
                as_queryset=True,
            )

            output = transformer.apply_from_database_and_selector(
                selector=search_db.selector,
                datatable=unique_queryset,
                select_kwargs=dict(
                    fitness_column=search_db.fitness_field,
                    # query_limit=200,  # OPTIMIZE: Smarter way to do this...?
                ),
                validators=[validator],
            )

            # if the source failed to create a structure, then we want to remove
            # it to prevent repeated issues.
            if output == False:
                # TODO: consider more advanced logic for changing the steady
                # state values of each source -- rather than just disabling
                # them here.
                logging.warning(
                    "Failed to create new individual with steady-state "
                    f"source {source_db.name}. Removing steady-state."
                )
                source_db.nsteadystate_target = 0
                source_db.save()
                shutil.rmtree(directory)
                return

            # otherwise we have a successful output that we can use
            parent_ids, new_structure = output
            source = {
                "transformation": source_db.name,
                "parent_ids": parent_ids,
            }

        elif source_db.is_creator:
            creator = source_db.to_toolkit()

            new_structure = creator.create_structure_with_validation(
                validators=[validator],
            )
            source = {
                "creator": source_db.name,
            }

        # if structure creation was successful, run the workflow for it
        if new_structure:
            state = search_db.subworkflow.run(
                structure=new_structure,
                source=source,
                directory=directory,  # BUG: consider making subfolder
                **search_db.subworkflow_kwargs,
            )
            result = state.result()
            # NOTE: we tell the workflow to use the same directory. There is
            # good chance the user indicates that they want to compress the
            # folder to.

            # check the final structure with our validator again. This populates
            # the fingerprint database (if one is being used).
            validator.check_structure(result.to_toolkit())
            # BUG: I think there is a race condition here... Other NewIndividual
            # workflows may try to populate the fingerprint at the START of
            # a run while this one must do it after .result() is called.

        # TODO: when I allow a series of subworkflows, I can do validation checks
        # between each run.
        # if a validator was given, we want to check the current structure
        # and see if it passes our test. This is typically only done in
        # expensive analysis -- like evolutionary searches
        # current_structure = result.to_toolkit()
        # if validator and not validator.check_structure(current_structure):
        #     # if it fails the check, we want to stop the series of calculations
        #     # and just exit the workflow run. We can, however, update the
        #     # database entry with the final structure.
        #     logging.info(
        #         "Did not pass validation checkpoint. Stopping workflow series."
        #     )
        #     return {"structure": current_structure}
