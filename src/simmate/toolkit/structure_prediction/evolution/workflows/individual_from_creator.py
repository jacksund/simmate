# -*- coding: utf-8 -*-

from simmate.toolkit import Composition
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow
from simmate.database.workflow_results import EvolutionarySearch
import simmate.toolkit.creators as creation_module


class StructurePrediction__Python__IndividualFromCreator(Workflow):

    use_database = False

    @staticmethod
    def run_config(
        search_id: int,
        creator_class_str: str,  # Union[str, StructureCreator]
        composition: Composition,
        subworkflow_name: str,
        subworkflow_kwargs: dict = {},
        **kwargs,
    ):
        # Consider moving to _deserialize_parameters. Only issue is that
        # I can't serialize these classes yet.
        if isinstance(creator_class_str, str):
            creator_class = getattr(creation_module, creator_class_str)
            creator = creator_class(composition)  # consider adding kwargs
        else:
            raise Exception(f"Creator class {creator_class_str} could not be found.")

        search_db = EvolutionarySearch.objects.get(id=search_id)

        new_structure = creator.create_structure_with_validation(
            validators=[],
            max_attempts=100,
        )

        # if structure creation was successful, run the workflow for it
        if new_structure:
            subworkflow = get_workflow(subworkflow_name)
            state = subworkflow.run(
                structure=new_structure,
                source={
                    "creator": creator_class_str,
                },
                **subworkflow_kwargs,
            )
            result = state.result()
