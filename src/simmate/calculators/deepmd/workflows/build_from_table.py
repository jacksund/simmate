# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset
from simmate.toolkit import Composition
from simmate.website.workflows import models as all_datatables
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow

# from simmate.database.workflow_results import Dynamics


class MlPotential__Deepmd__BuildFromTable(Workflow):

    use_database = False

    def run_config(
        composition: Composition,
        directory: Path,
        table_name: str,
        filter_kwargs: dict = {},
        **kwargs,
    ):

        # Load the desired table and filter the target structures from it
        #
        # Import the datatable class -- how this is done depends on if it
        # is from a simmate supplied class or if the user supplied a full
        # path to the class
        # OPTIMIZE: is there a better way to do this?
        if hasattr(all_datatables, table_name):
            datatable = getattr(all_datatables, table_name)
        else:
            raise Exception("Unknown table name provided")
        #
        all_db_structures = datatable.objects.filter(
            formula_reduced=composition.reduced_formula, **filter_kwargs
        )
        # TODO:
        # - make a get_table utility
        # - check that the table has both Thermo and Forces mix-ins
        # - chunk queryset if it's +1million structures
        # - add warning if workflow_name isn't in the filters

        if not all_db_structures:
            raise Exception(
                "There are no results for the table+filter settings given."
                "Either populate your table with calculations or change "
                "your filtering criteria."
            )

        # write structure data to files for use with deepmd
        training_data, testing_data = DeepmdDataset.to_file(
            ionic_step_structures=all_db_structures,
            directory=directory / "deepmd_data",
        )
        # TODO: consider splitting into separate datasets and training with
        # data in stages

        deepmd_directory = directory / "deepmd"

        # grab the deepmd training workflow and run the first step
        deepmd_workflow = get_workflow("ml-potential.deepmd.train-model")

        deepmd_workflow.run(
            directory=deepmd_directory,
            composition=composition,
            command='eval "$(conda shell.bash hook)"; conda activate deepmd; dp train input.json > deepmd.out',
            training_data=training_data,
            testing_data=testing_data,
            # TODO: consider making a subdirectory for deepmd
        )
