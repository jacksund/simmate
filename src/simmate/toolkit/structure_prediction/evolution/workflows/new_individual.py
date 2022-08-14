# -*- coding: utf-8 -*-


from simmate.workflow_engine import Workflow
from simmate.database.workflow_results import EvolutionarySearch


class StructurePrediction__Python__NewIndividual(Workflow):

    use_database = False

    @staticmethod
    def run_config(
        search_id: int,
        structure_source_id: int,
        **kwargs,
    ):

        search_db = EvolutionarySearch.objects.get(id=search_id)
        source_db = search_db.structure_sources.get(id=structure_source_id)

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
                **search_db.subworkflow_kwargs,
            )
            result = state.result()
