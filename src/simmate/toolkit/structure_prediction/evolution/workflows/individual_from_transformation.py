# -*- coding: utf-8 -*-

from simmate.toolkit import Composition
import simmate.toolkit.transformations.from_ase as transform_module
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow


class StructurePrediction__Python__IndividualFromTransformation(Workflow):

    use_database = False

    @staticmethod
    def run_config(
        search_id: int,
        transformation_class_str: str,  # Union[str, StructureTransformation]
        selector_class_str: str,
        composition: Composition,
        subworkflow_name: str,
        subworkflow_kwargs: dict = {},
        **kwargs,
    ):
        # Consider moving to _deserialize_parameters. Only issue is that
        # I can't serialize these classes yet.
        if transformation_class_str in [
            "from_ase.Heredity",
            "from_ase.SoftMutation",
            "from_ase.MirrorMutation",
            "from_ase.LatticeStrain",
            "from_ase.RotationalMutation",
            "from_ase.AtomicPermutation",
            "from_ase.CoordinatePerturbation",
        ]:
            # all start with "from_ase" so I assume that import for now
            ase_class_str = transformation_class_str.split(".")[-1]
            transformation_class = getattr(transform_module, ase_class_str)
            return transformation_class(composition)
        # !!! There aren't any common transformations that don't accept composition
        # as an input, but I expect this to change in the future.
        elif transformation_class_str in []:
            transformation_class = getattr(transform_module, transformation_class_str)
            transformer = transformation_class(composition)
        else:
            raise Exception(
                f"Transformation class {transformation_class_str} could not be found."
            )

        search_db = EvolutionarySearch.objects.get(id=search_id)

        # new_structure = transformer.apply_from_database_and_selector(
        #     selector,
        #     datatable=search_db.individuals_completed,
        #     selector_kwargs: dict = {},
        #     max_attempts: int = 100,
        #     validators=[],
        #     max_attempts=100,
        # )

        # if structure creation was successful, run the workflow for it
        if new_structure:
            workflow = get_workflow(subworkflow_name)
            state = workflow.run(
                structure=new_structure,
                source={
                    "transformation": transformation_class_str,
                    "parent_ids": parent_ids,
                },
                **subworkflow_kwargs,
            )
            result = state.result()
