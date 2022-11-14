# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset
from simmate.toolkit import Structure
from simmate.toolkit import Composition
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow
from simmate.website.workflows import models as all_datatables

from statistics import mean 

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

# re-run train/test until all structures <5% error


class MlPotential__Deepmd__BuildFromParallel(Workflow):

    use_database = False

    def run_config(
        structure: Structure,
        directory: Path,
        init_data: str,  # set to either 'md' or 'table', make md default setting??
        composition: Composition, 
        test_option: str, # set to either 'lammps' or 'rand_struct' 
        table_name: str = "",
        num_models: int = 3, #assuming that deepmd randomly selects seeds
        max_error: float = 0.5, 
        filter_kwargs: dict = {},
        md_kwargs: dict = {"temperature_start": 300, "temperature_end": 300, "nsteps" : 1000},
    ):
        
        #---------- START STRUCT ---------
        #grab prototype of composition if structure not given             
        
        # ---------- START DATA ----------
        # if user sets init_data to 'md', generate a list of starting structures from an md run 
        
        if init_data == 'md':
            
            md_workflow = get_workflow("dynamics.vasp.mit")
        
            state = md_workflow.run(
                structure=structure,
                **md_kwargs,
                )     
            
            start_structs = state.result().structures.all()
            
        #if user sets init_data to 'table', generate a list of starting  
        #structures from an existing table    
        elif init_data == 'table':
            
            if hasattr(all_datatables, table_name):
                datatable = getattr(all_datatables, table_name)
            else:
                raise Exception("Unknown table name provided")
                
            start_structs = datatable.objects.filter(
                formula_reduced=composition.reduced_formula, **filter_kwargs
            ).order_by("energy_per_atom")
            
            if not start_structs:
                raise Exception(
                    "There are no results for the table+filter settings given."
                    "Either populate your table with calculations or change "
                    "your filtering criteria."
                )
                
        else:
            raise Exception("Parameter init_data must be either 'md' or 'table'")
        
        #set up directory to hold deepmd data files and runs
        #this folder will hold all deepmd data sets and all information from training steps
        deepmd_directory = directory / "deepmd"

        #create running list of training/testing data
        #this list will be appended as more data sets are created 
        training_data = []
        testing_data = []
        
        #create deepmd datasets for initial structures 
        train, test = DeepmdDataset.to_file(
            ionic_step_structures=start_structs,
            directory=deepmd_directory / "deepmd_data_init",
        )

        training_data += train
        testing_data += test
        
        # ------- INITIAL TRAINING -------
        
        deepmd_workflow = get_workflow("ml-potential.deepmd.train_model")

        # concurrently train specified number of models 
        for num in range(num_models):
            
            deepmd_workflow.run(  # ---------------- USE RUN CLOUD IN FINAL VERSION
                directory=deepmd_directory / f'run_{num}', #remove if using run cloud
                composition=structure.composition,
                command=f'eval "$(conda shell.bash hook)"; conda activate deepmd; dp train input_{num}.json',
                input_filename="input_{num}.json",
                training_data=training_data,
                testing_data=testing_data,
                )
            
            freeze_workflow = get_workflow("ml-potential.deepmd.freeze_model")
            
            #freeze_model         
            freeze_workflow.run(
                command = f"dp freeze -o graph_{num}.pb",
                directory=deepmd_directory / f'run_{num}', #how to set this if using run cloud???
            )
            
            #search for graph file name and add to list? 
            #make variable/return graph name in freeze workflow
            
            model_list = [] 
            
            
            #!!!at this point you have x number of models that need to be tested
        
        # ---------- TEST MODELS (MD opt) ----------
        
        if test_option == "md":
            
            prediction_workflow = get_workflow("ml-potential.deepmd.get_force_energy")
        
            lammps_workflow = get_workflow("ml-potential.deepmd.run_lammps")
            
            static_energy_workflow = get_workflow("static-energy.vasp.mit")
            
            #set up directory to hold lammps data files and runs 
            lammps_directory = directory / "lammps"
            
            
            #make counter to keep track of the number of testing/retraining iterations
            counter = 0 
            while True:
                
                #run initial lammps simulation with first trained model 
                lammps_workflow.run(
                    structure = structure, #randomly create a new structure for this instead??
                    directory = lammps_directory / f"test_{counter}",
                    deepmd_model = model_list[0], 
                    lammps_timestep = 1000)
                
                #get energy and forces from lammps 
                #hold lammps data in a table so grab directly from there?? 
                lammps_energy = []
                lammps_forces = [] 
                
                #get structures from lammps 
                lammps_structures = []
                
                #create a list to hold new structures that will be incorperated
                #into later training steps 
                new_training_structs = []
                
                for n,struct in enumerate(lammps_structures):
                    energy_errors = []
                    for model in model_list[1:]:
                        #!!! problem with workflow, having to create calculator each time its called 
                       state = prediction_workflow.run(
                            structure = struct,
                            deepmd_model = model)
                       
                       predicted_energy, predicted_force_field = state.result()
                       
                       #calculate the error between the energy predicted in lammps with model 0
                       #and the energy predicted using the calculator with other models 
                       error = (abs(lammps_energy[n]-predicted_energy))/lammps_energy[n] 
                       
                       #add calculated error to running list 
                       energy_errors.append(error)
                       
                    #calculate the average error for structure n 
                    average_error = mean(energy_errors)
                    
                    #if the average energy of the structure is 
                    if average_error > max_error:
                        new_training_structs.append(struct)
                
                #if there are less than x number of structures above the error
                #don't bother retraining and end loop 
                if len(new_training_structs) < 20:
                    break 
                
                #calculate properties for each new training structure
                for struct in new_training_structs:
                    static_energy_workflow.run(
                        structure = struct,
                        )
                    
                # how to create query set with just these structures???
                train, test = DeepmdDataset.to_file(
                    ionic_step_structures=start_structs,
                    directory=deepmd_directory / f"deepmd_data_{counter}",
                    )
                
                #add new data sets to list 
                training_data += train
                testing_data += test
                
                #!!!everything below needs to happen in each of the directories
                #used to intially run deepmd 
                
                #find newest available checkpoint 
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

                command = f'eval "$(conda shell.bash hook)"; conda activate deepmd; dp train --restart {checkpoint_file.stem} input_{n}.json'
                
                counter +=1 
                
                
                deepmd_workflow.run(
                    directory=deepmd_directory / f'run_{counter}', #setting directory with cloud???
                    composition=structure.composition,
                    command=command,
                    input_filename="input_{counter}.json",
                    training_data=training_data,
                    testing_data=testing_data,
                    )
                
                
                
                
                
                
                
                
                