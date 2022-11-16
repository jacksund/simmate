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
from ase import units

from deepmd.calculator import DP

from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow


class MlPotential__Deepmd__AseMD(Workflow):
    
    def config(structure: Structure, 
               directory: Path,
               deepmd_model: str = 'graph.pb',
               nsteps: int = 1000,
               **kwargs):
        
        #convert structure to ASE atom type 
        atoms = AseAtomsAdaptor(structure)
        
        #set calculator to deepmd model 
        calculator = DP(model=directory / deepmd_model)        
    
        atoms.calc = calculator
        
        #set the momenta corresponding to T=300K
        MaxwellBoltzmannDistribution(atoms, temperature_K=300)
        
        dyn = VelocityVerlet(atoms, dt=5.0 * units.fs,
                     trajectory='ase_md.traj', logfile='ase_md.log')
        
        #run dynamics for nsteps
        dyn.run(nsteps)  
        



    