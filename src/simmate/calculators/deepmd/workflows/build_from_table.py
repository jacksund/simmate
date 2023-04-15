# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset
from simmate.toolkit import Composition
from simmate.utilities import chunk_list
from simmate.website.workflows import models as all_datatables
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow

class MlPotential__Deepmd__BuildFromTable(Workflow):

    use_database = False

    def run_config(
        composition: Composition,
        directory: Path,
        table_name: str,
        start_from_model: bool=False,
        filter_kwargs: dict = {},
        deepmd_settings: dict ={},
        deepmd_training_steps: int = 10000000,
        training_iterations: int = 1,  # setting to 1 means no iterative training
        **kwargs,
    ):

        overall_directory = directory
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

        # sort db structures by energy per atom
        all_db_structures = datatable.objects.filter(
            formula_reduced=composition.reduced_formula, **filter_kwargs
        ).order_by("energy_per_atom")

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

        # set directory to run deepmd in
        deepmd_directory = directory / "deepmd"

        # grab the deepmd training workflow
        deepmd_workflow = get_workflow("ml-potential.deepmd.train-model")

        # divide overall query into equal sized list of structures
        # !!!throws error if list cannot be divided equally 
        structs_per_chunk = int(all_db_structures.count() / training_iterations)

        # We want to train in stages, so we split the queryset into smaller
        # groups. We want the subsets each as a pandas dataframe for the
        # DeepmdDataset input too.
        structure_lists = chunk_list(
            all_db_structures.to_dataframe(),
            structs_per_chunk,
        )

        # have list of training_data and testing_data
        training_data = []
        testing_data = []

        for n, sublist in enumerate(structure_lists):

            # create training/testing files for the chunk of strutures
            train, test = DeepmdDataset.to_file(
                ionic_step_structures=sublist,
                directory=directory / f"deepmd_data_{n}",
            )

            training_data += train
            testing_data += test
            
            #check if training has to be restarted or if starting from scratch 
            if start_from_model:
                # find the newest available checkpoint file
                number_max = 0  # to keep track of checkpoint number
                checkpoint_file = None
                for file in deepmd_directory.iterdir():
                    if "model.ckpt" in file.stem and "-" in file.stem:
                        number = int(file.stem.split("-")[-1])
                        if number > number_max:
                            number_max = number
                            checkpoint_file = file
                # make sure the loop above ended with finding a file
                if not checkpoint_file:
                    raise Exception("Unable to detect DeepMD checkpoint file")

                command = f'dp train --restart {checkpoint_file.stem} input_{n}.json'
                num_training_steps = number_max + deepmd_training_steps

                deepmd_workflow.run(
                    directory=deepmd_directory,
                    composition=composition,
                    command=command,
                    input_filename=f"input_{n}.json",
                    num_training_steps = num_training_steps,
                    training_data=training_data,
                    testing_data=testing_data,
                    settings_update = deepmd_settings,)   
            
            else:
                
                if n == 0:
                    command = f'dp train input_{n}.json'
                    num_training_steps = deepmd_training_steps
                
                else:
    
                    # find the newest available checkpoint file
                    number_max = 0  # to keep track of checkpoint number
                    checkpoint_file = None
                    for file in deepmd_directory.iterdir():
                        if "model.ckpt" in file.stem and "-" in file.stem:
                            number = int(file.stem.split("-")[-1])
                            if number > number_max:
                                number_max = number
                                checkpoint_file = file
                    # make sure the loop above ended with finding a file
                    if not checkpoint_file:
                        raise Exception("Unable to detect DeepMD checkpoint file")
    
                    command = f'dp train --restart {checkpoint_file.stem} input_{n}.json'
                    num_training_steps = number_max + deepmd_training_steps
    
                deepmd_workflow.run(
                    directory=deepmd_directory,
                    composition=composition,
                    command=command,
                    input_filename=f"input_{n}.json",
                    num_training_steps = num_training_steps,
                    training_data=training_data,
                    testing_data=testing_data,
                    settings_update = deepmd_settings,
                )

        freeze_workflow = get_workflow("ml-potential.deepmd.freeze-model")

        #!!!allow passing of unique name for deepmd graph file
        freeze_workflow.run(
            directory=deepmd_directory,
        )
        
        return overall_directory  
