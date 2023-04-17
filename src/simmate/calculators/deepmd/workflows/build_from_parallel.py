# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 12:21:46 2023

@author: siona
"""

#User enters: composition for random structures, settings to use with build-from-md or build-from-table

#TODO
  #properly filter structures from the database using the id
  #explicitly import the build_from_table workflow
  #add way to conitnue model training with build-from-table method
  
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
            composition: Composition,
            directory: Path,
            init_model: str, #either md or table 
            init_model_kwargs: dict = {},
            num_test_structs: int = 100,
            rand_generator_attempts: int =1000,
            num_models: int = 3,
            max_error: float = 0.5, 
            max_attempts: int = 5,
            **kwargs,
            ):
        
        #import initial model training method 
        if init_model == 'md':
            init_model_training = get_workflow('ml-potential.deepmd.build-from-md')
        elif init_model == 'table':
            init_model_training = get_workflow('ml-potential.deepmd.build-from-table')
        else:
            raise Exception("Invalid method entered for initial model training")
            
        print(init_model + ' loaded')
        
        #import build from table workflow
        build_from_table = get_workflow('ml-potential.deepmd.build-from-table')
        print('build from table loaded')

        
        #import static energy workflow         
        static_energy = get_workflow('static-energy.vasp.mit')
        static_energy.error_handlers = [] #turn error handlers off
        print('static energy loaded')
        
        #import random structure generation function 
        struct_generator = RandomSymWalkStructure(composition = composition,
                                                  max_total_attempt = rand_generator_attempts)
        
        print('structure generator loaded')

        
        #import energy/force prediction workflow 
        get_energy_force = get_workflow("ml-potential.deepmd.prediction")
        
        print('force/energy prediction loaded')

        

##INITIAL TRAINING OF MODELS
        
        #Begin by training multiple models using same starting structure/composition
        model_submitted_states = []
        for num in range(num_models):
            state = init_model_training.run(**init_model_kwargs)
            model_submitted_states.append(state)
        
        print('begin model training')
            
        #worklows returns the directory where the deepmd data/run files are 
        #stored so this will collect all the directories in one list
        directories = [state.result() for state in model_submitted_states]
        
##TRAINING LOOP WITH RAND STRUCTS 
        print('start of training loop')
        counter = 0 
        master_check = True 
        while master_check:
            #check the counter to see if the max number of cycles has been reached 
            if counter == max_attempts:
                master_check = False 
                
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
            print('test structures created')
            #Use each model created to predict the energies/forces for each randomly 
            #created structure
            deepmd_prediction_states = [] 
            for directory in directories:
                state = get_energy_force.run(directory = directory / "deepmd",
                                             structure = test_structures)
                deepmd_prediction_states.append(state)
            
            #Collect a dictionary for each model containing the predicted energies and forces
            #each list will contain the forces/energies predicted for each structure created 
            energy_force_list = [state.result() for state in deepmd_prediction_states]
            
            average_error = []
            #We start by iterating through the energies predicted by the first model 
            #and compare it to the energies predicted by all other models 
            print('checking errors')
            for n, e1 in enumerate(energy_force_list[0]['energies']):
                print(e1)
                error_list = []
                for energy_list in energy_force_list[1:]['energies']:
                    e2 = energy_list[n]
                    print(e2)
                    error = abs((e1 - e2)/e1)
                    print(error)
                    error_list.append(error)
                    
                average_diff = mean(error)
                average_error.append(average_diff)
            
            #Iterate through the average erorrs and see which structures show disagreement 
            #above the maximum error
            next_gen_structs = []
            for n, error in average_error:
                if error > max_error:
                    next_gen_structs.append(test_structures[n])
            print('structures added to list')
            #if there are less than 20 structures in next_gen_structs, don't 
            #bother retraining models 
            #!!!change to a percentage, let user decide??
            if len(next_gen_structs) < 20:
                master_check = False 
            
            #carry out static energy calculations for each of the structures 
            #!!!keep track of state id's to use build_from_table
            static_energy_states = []
            for struct in next_gen_structs:
                #use run cloud to run static energy calculations in parallel 
                state = static_energy.run_cloud(
                    structure=struct,
                )
                static_energy_states.append(state)
                
            structure_id = [state.result().id for state in static_energy_states]
            print('static calcs run')
            
            for directory in directories:
                state = build_from_table.run(composition = composition,
                                             directory = directory,
                                             table_name = 'StaticEnergy',
                                             start_from_model = True,
                                             filter_kwargs = {'id__range' : [structure_id[0], structure_id[-1]]},
                                             training_iterations = 1,)  # setting to 1 means no iterative training
                deepmd_prediction_states.append(state)
            print('build from table run')
            
         
            
            
            

        

        
            
            
            
            
            
        
        
