# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.deepmd.inputs.type_and_set import DeepmdDataset
from simmate.toolkit import Composition
from simmate.website.workflows import models as all_datatables
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow


class MlPotential__Deepmd__BuildFromTable(Workflow):

    use_database = False

    def run_config(
        composition: Composition,
        directory: Path,
        table_name: str,
        filter_kwargs: dict = {},
        md_kwargs: dict = {},
        #deepmd_kwargs: dict ={},
        training_iterations: int = 1, #setting to 1 means no iterative training 
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
        
        #sort db structures by energy per atom
        all_db_structures = datatable.objects.filter(
            formula_reduced=composition.reduced_formula, **filter_kwargs
        ).order_by('energy_per_atom')
        
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
        
        #set the directory to run deepmd in 
        deepmd_directory = directory / "deepmd"
        
        # grab the deepmd training workflow
        deepmd_workflow = get_workflow("ml-potential.deepmd.train-model")
        
        #divide overall query into equal sized list of structures 
        num_structs = all_db_structures.count()/training_iterations
            
        structure_lists = chunk_list(all_db_structures, num_structs)
            
        #have list of training_data and testing_data
        training_data = []
        testing_data = []
            
        for n, item in structure_lists:
            #create training/testing files for each chunk of strutures 
            train, test = DeepmdDataset.to_file(
                ionic_step_structures=item,
                directory = directory / f"deepmd_data_{n}")
                
            training_data.append(train)
            testing_data.append(test)
                
            deepmd_workflow.run(
                directory=deepmd_directory,
                composition=composition,
                command=f'eval "$(conda shell.bash hook)"; conda activate deepmd; dp train input{n}.json > deepmd.out',
                training_data=training_data,
                testing_data=testing_data,
                    )
                
        
        '''      
        # write structure data to files for use with deepmd
        training_data, testing_data = DeepmdDataset.to_file(
            ionic_step_structures=all_db_structures,
            directory=directory / "deepmd_data",
            )
            

        deepmd_workflow.run(
            directory=deepmd_directory,
            composition=composition,
            command='eval "$(conda shell.bash hook)"; conda activate deepmd; dp train input.json > deepmd.out',
            training_data=training_data,
            testing_data=testing_data,
            # TODO: consider making a subdirectory for deepmd
        )
        '''