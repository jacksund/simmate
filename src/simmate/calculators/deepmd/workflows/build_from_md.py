# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset
from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow

class MlPotential__Deepmd__BuildFromMd(Workflow):

    use_database = False

    def run_config(
        structure: Structure,
        directory: Path,
        start_from_model: bool=False,
        temperature_list: list[int] = [300, 750, 1200],
        relax_start_structure: bool = True, 
        relax_kwargs: dict = {},
        md_kwargs: dict = {}, 
        deepmd_settings: dict =  {},
        **kwargs,
    ):

        # Check if the user wants to relax the starting structure 
        # If true (default), relax structure and set as starting structure 
        if relax_start_structure:
            relax_workflow = get_workflow(
                "relaxation.vasp.mit"
            )  #!!!set to higher quality or allow quality to be set by user
            state = relax_workflow.run(
                structure=structure,
                directory=directory / relax_workflow.name_full,
                **relax_kwargs,
            )
            start_struct = state.result()
        else:
            start_struct = structure 

        # For each temperature submitted by user, submit a md run to cloud to run in parallel
        md_workflow = get_workflow("dynamics.vasp.mit")
        submitted_states = []
        for temperature in temperature_list:
            
            #use run cloud to run dynamics in parallel 
            state = md_workflow.run_cloud(
                structure=start_struct,
                temperature_start=temperature,
                temperature_end=temperature,  # constant temp for entire run
                **md_kwargs,
            )
            submitted_states.append(state)

        # Wait for all dynamics runs to finish (only if you're running with run cloud?)
        results = [state.result() for state in submitted_states]

        # Iterate through the results of each md simulation and get
        # temperature and list of ionic steps
        # Write structure data to files for use with deepmd
        for result in results:
            temp = result.temperature_start
            structures = result.structures.all()
            DeepmdDataset.to_file(
                ionic_step_structures=structures,
                directory=directory / f"deepmd_data_{temp}",
            )

        # training files are named after the composition. To get this, we can
        # simply use the first result (all should be the same)
        composition = results[0].formula_full
        
        # keep a running list of training and test datasets. We slowly add to
        # this list as we train
        training_data = []
        testing_data = []
        
        if not start_from_model:

            # INITIAL DEEPMD TRIANING ITERATION
            temperature = temperature_list[0]
            
            #Add datasets from first temperature to overall training/testing lists
            training_data.append(
                directory / f"deepmd_data_{temperature}/{composition}_train"
            )
            testing_data.append(
                directory / f"deepmd_data_{temperature}/{composition}_test"
            )
    
            deepmd_directory = directory / "deepmd"
    
            # Grab the deepmd training workflow and run the first step
            deepmd_workflow = get_workflow("ml-potential.deepmd.train-model")
            
            deepmd_workflow.run(
                directory=deepmd_directory,
                composition=structure.composition,
                command='dp train input_1.json',
                input_filename="input_1.json",
                training_data=training_data,
                testing_data=testing_data,
                settings_update = deepmd_settings,
            )
            
            #ITERATIVE TRIANING STEPS (only if multiple temperatures are submitted) 
            if len(temperature_list) > 1:
                # run additional deepmd training iterations with restart function
                for n, temperature in enumerate(temperature_list[1:]):
                    
                    # add the new dataset to our list
                    training_data.append(
                        directory / f"deepmd_data_{temperature}/{composition}_train"
                    )
                    testing_data.append(
                        directory / f"deepmd_data_{temperature}/{composition}_test"
                    )
        
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
                    
                    # And continue the model training with this new data
                    deepmd_workflow.run(
                        directory=deepmd_directory,
                        composition=structure.composition,
                        command=f'dp train --restart {checkpoint_file.stem} input_{n}.json',
                        input_filename=f"input_{n}.json",
                        num_training_steps = number_max*2,
                        training_data=training_data,
                        testing_data=testing_data,
                    )
                
        else:
            for n, temperature in enumerate(temperature_list):
    
                # add the new dataset to our list
                training_data.append(
                    directory / f"deepmd_data_{temperature}/{composition}_train"
                )
                testing_data.append(
                    directory / f"deepmd_data_{temperature}/{composition}_test"
                )
    
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
    
                # And continue the model training with this new data
                deepmd_workflow.run(
                    directory=deepmd_directory,
                    composition=structure.composition,
                    command=f'dp train --restart {checkpoint_file.stem} input_{n}.json',
                    input_filename=f"input_{n}.json",
                    num_training_steps = number_max*2,
                    training_data=training_data,
                    testing_data=testing_data,
                )
            
        freeze_workflow = get_workflow("ml-potential.deepmd.freeze-model")

        #!!!allow passing of unique name for deepmd graph file
        freeze_workflow.run(directory=deepmd_directory)
        
        return directory
        
