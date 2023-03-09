# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 12:21:46 2023

@author: siona
"""
# training multiple models at the same time

# ---------- START DATA ----------
# if no input structure, use common prototypes (e.g. BCC)
    # need at least composition? 
# get starting data (either md run or from table)

# ---------- TRAIN ----------
# train models for 1 iteration

# ---------- TEST MODELS (MD opt) ----------

# if no input structure, use common prototypes (e.g. BCC)
# run short lammps simulation (1000 steps) using ONE of the deepmd models

# pull the output structures from the lammps run and use the OTHER deepmd models
# to predict energy/forces

# Compare energy/forces across all structures & models. Ones that differ the
# most (i.e. models are most uncertain) should be calculated with DFT and added
# to the training/test set.
# (maybe grab N structures randomly from those with +5% error)

# make new datasets after each iteration

# ---------- TEST MODELS (Random struct opt) ----------

# randomly create a series of new structures

# (option 1)
# predict energy/forces for ALL structures using ALL models

# (option 2)
# Relax ALL structures using ONE model. Store ionic steps + energies + forces.
# Pull the output structures from the lammps run and use the OTHER deepmd models
# to predict energy/forces. 

# (option 3)
# Run MD simulations on ALL structures using ONE model --> follow MD opt above

# Compare energy/forces across all structures & models. Ones that differ the
# most (i.e. models are most uncertain) should be calculated with DFT and added
# to the training/test set.
# (maybe grab N structures randomly from those with +5% error)

# make new datasets after each iteration

# ---------- STOP CONDITION ----------

# relax input structure
# run interation of build_from_md and grab location of deepmd runs 
    # run with one temperature 
# create random structures and preduct energy/forces with models and with dft 

from pathlib import Path

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset
from simmate.toolkit import Structure, Composition 
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow
from simmate.website.workflows import models as all_datatables
from simmate.toolkit.creators.structure.random_symmetry_walk import RandomSymWalkStructure

from statistics import mean 

class MlPotential__Deepmd__BuildFromParallel(Workflow):
    
    use_database = False
    
    def run_config(
            structure: Structure,
            directory: Path,
            composition: Composition = None, #if using build from table option 
            md_temperature_list: list = [1200],
            build_from_md_kwargs: dict = None,
            num_test_structs: int = 100,
            num_models: int = 3,
            max_error: float = 0.5, 
            max_attempts = 5,
            **kwargs,
            ):
        
        #import build_from_md workflow 
        build_from_md = get_workflow('ml-potential.deepmd.build_from_md')
        
        #import random structure generation function
        struct_generator = RandomSymWalkStructure(composition = structure.composition)
        
        #import energy/force prediction workflow 
        get_energy_force = get_workflow()
        
        #import deepmd training workflow 
        deepmd_workflow = get_workflow("ml-potential.deepmd.train-model")
        
        #import freeze model workflow 
        freeze_workflow = get_workflow("ml-potential.deepmd.freeze-model")

##INITIAL TRAINING OF MODELS
        
        #Begin by training multiple models using same starting structure 
        model_submitted_states = []
        for num in range(num_models):
            state = build_from_md.run(structure = structure,
                                      temperature_list = md_temperature_list,
                                      **build_from_md_kwargs)
            model_submitted_states.append(state)
            
        #The build_from_md worklow returns the directory where the deepmd data/run files are 
        #stored so this will collect all the directories in one list
        deepmd_directories = [state.result() for state in model_submitted_states]
        
##TRAINING LOOP WITH RAND STRUCTS 
        counter = 0 
        master_check = True 
        while master_check:
            counter +=1 
            #Create random structures to test each model with and to use as training
            #data for the next step 
            test_structures = []
            while len(test_structures) < num_test_structs:
                new_struct = struct_generator.new_structure() 
                if new_struct == False:
                    continue
                else:
                    test_structures.append(new_struct) 
            
            #Use each model created to predict the energies/forces for each randomly 
            #created structure
            deepmd_prediction_states = [] 
            for directory in deepmd_directories:
                state = get_energy_force.run(directory = directory/'deepmd',
                                             structure = test_structures)
                deepmd_prediction_states.append(state)
            
            #Collect a dictionary for each model containing the predicted energies and forces
            #each list will contain the forces/energies predicted for each structure created 
            energy_force_list = [state.result() for state in deepmd_prediction_states]
            
            average_error = []
            #start by iterating through the first list 
            for e1 in energy_force_list[0]['energies']:
                error_list = []
                for e2 in energy_force_list[1:]['energies']:
                    error = abs((e1 - e2)/e1)
                    error_list.append(error)
                    
                average_diff = mean(error)
                average_error.append(average_diff)
                
            next_gen_structs = []
            for n, error in average_error:
                if error > max_error:
                    next_gen_structs.append(test_structures[n])
            
            #if there are less than 20 structures in next_gen_structure, don't 
            #bother retraining models 
            if len(next_gen_structs) < 20:
                master_check = False 
                
            if counter > max_attempts:
                master_check = False 
            
            #create lists to hold new training/testing data
            #!!!CAN REPLACE THE SECTION BELOW WITH THE BUILD_FROM_TABLE METHOD 
            #if new_structs are added to a database?  
            training_data = []
            testing_data =[] 
            ##RESTART TRAINING (run in parallel!!!) 
            for directory in deepmd_directories:
                #create datasets for the new trianing strucutres in each model directory
                DeepmdDataset.to_file(
                    ionic_step_structures=next_gen_structs,
                    #!!!check directory name!!!
                    directory = directory / f"deepmd_data_randstruct_{counter}",
                )
                #add new datasets to running list of training/testing data 
                training_data.append( directory / f"deepmd_data_randstruct_{counter}_train")
                testing_data.append( directory / f"deepmd_data_randstruct_{counter}_test")
                # find the newest available checkpoint file
                number_max = 0  # to keep track of checkpoint number
                checkpoint_file = None
                for file in directory.iterdir():
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
                    directory=directory,
                    composition=structure.composition,
                    command=f'dp train --restart {checkpoint_file.stem} input_{n}.json',
                    input_filename=f"input_{n}.json",
                    training_data=training_data,
                    testing_data=testing_data,
                )
                #freeze model once training is complete 
                freeze_workflow.run(directory=directory)
                
                #!!!make sure model.pb file gets overridden!!!


            
            
                    
                    
                
            
                
                    
              
                
                    
                    
                
                
                
            
                
            
            
        
        
     
                
            
            
      
        
        
        
        
        
        
        
        
            
        
            
            
            
        
        
        
        
        
        
        
        

        
            
            
            
            
            
        
        
