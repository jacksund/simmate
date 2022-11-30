# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14 11:52:56 2022

@author: siona
"""

#Use ASE to run molecular dynamics 
from pathlib import Path

from pymatgen.io.ase import AseAtomsAdaptor

from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.md.verlet import VelocityVerlet
from ase.io.trajectory import Trajectory
from ase import units

from deepmd.calculator import DP

from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow


class MlPotential__Deepmd__AseMD(Workflow):
    
    use_database = False
    
    def run_config(
               structure: Structure,
               deepmd_model: str = 'graph.pb', #set to directory where model file is located
               temperature: int = 300, 
               nsteps: int = 10000,
               trajectory_file: str = 'ase_md.traj',
               log_file: str = 'ase_md.log',
               **kwargs):
                
        #convert structure to ASE atom type 
        atoms = AseAtomsAdaptor.get_atoms(structure)
        
        #set calculator to deepmd model 
        calculator = DP(model=deepmd_model)        
    
        atoms.calc = calculator
        
        #set the momenta corresponding to given temperature 
        MaxwellBoltzmannDistribution(atoms, temperature_K=temperature)
        
        dyn = VelocityVerlet(atoms, dt=5.0 * units.fs,
                     trajectory= trajectory_file, logfile=log_file)
        
        #run dynamics for nsteps
        #calculate/return energy and forces while dynamics is running 
        dyn.run(nsteps)  
        
        
        ase_atoms = Trajectory(trajectory_file)

        #convert atoms objects to pymatgen structure objects 
        pym_structs = []
        for struct in ase_atoms:
            pym_structs.append(AseAtomsAdaptor.get_structure(struct))
            
        return {'structures':pym_structs}
            
        
        
        



    