# -*- coding: utf-8 -*-

import logging
import shutil
from pathlib import Path

from simmate.toolkit.structure_prediction.evolution.database.fixed_composition import (
    FixedCompositionSearch,
)
from simmate.workflow_engine import Workflow


class StructurePrediction__Toolkit__NewIndividual(Workflow):
    """
    Generates a new individual for an evolutionary search algorithm.

    Note, this workflow should not be called directly, but instead used within
    higher level workflows (such as `fixed-composition`)
    """

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
            parent_ids, new_structure = transformer.apply_from_database_and_selector(
                selector=search_db.selector,
                datatable=search_db.individuals_completed,
                select_kwargs=dict(
                    ranking_column=search_db.fitness_field,
                    query_limit=200,  # Smarter way to do this...?
                ),
                validators=[search_db.validator],
            )
            source = {
                "transformation": source_db.name,
                "parent_ids": parent_ids,
            }

        elif source_db.is_creator:

            creator = source_db.to_toolkit()

            new_structure = creator.create_structure_with_validation(
                validators=[search_db.validator],
            )
            source = {
                "creator": source_db.name,
            }

        # if structure creation was successful, run the workflow for it
        if new_structure:
            state = search_db.subworkflow.run(
                structure=new_structure,
                source=source,
                directory=directory,
                **search_db.subworkflow_kwargs,
            )
            result = state.result()
            # NOTE: we tell the workflow to use the same directory. There is
            # good chance the user indicates that they want to compress the
            # folder to.
