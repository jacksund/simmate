# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 10:30:24 2022

@author: siona
"""

from pathlib import Path

from pymatgen.io.ase import AseAtomsAdaptor
from deepmd.calculator import DP 

from simmate.workflow_engine import Workflow
from simmate.toolkit import Structure



class MlPotential__Deepmd__Prediction(Workflow):
    
    use_database = False
    
    def run_config(
            structure: Structure, #structure to be tested 
            directory: Path, #directory where model (graph.pb) file is stored 
            ):
        
        #set deepmd trained model as calculator
        #assuming name is graph.pb but this depends on what name was used in freeze_model workflow
        #!!!if doesn't work, set type_dict
        calculator = DP(model = 'graph.pb')  
        
        #get ase atoms from structure 
        structure_atoms = AseAtomsAdaptor.get_atoms(structure)
        
        #set calculator for ase object to deepmd calculator 
        structure_atoms.calc = calculator 
        
        deepmd_energy = structure_atoms.get_potential_energy()
        
        deepmd_forces = structure_atoms.get_forces()
        
        #can deepmd model be used to predict other parameters??
        
        return {"energy": deepmd_energy, "forces": deepmd_forces}
        
        
        
        
        
        
        
        
        
        
        
        
        
    
