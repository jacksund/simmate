# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 15:52:56 2023

@author: siona
"""

#Use ASE to run optimizations 
from pathlib import Path

from deepmd.calculator import DP

from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow

from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.core.structure import Structure 

from ase.optimize import BFGS 
from ase.io.trajectory import Trajectory

class MlPotential__Deepmd__AseOptimize(Workflow):
    
    use_database = False
    
    def run_config(
               structure: Structure,
               source: dict = None,
               directory: Path,
               deepmd_model: str = 'graph.pb', 
               fmax: int = 0.05, 
               max_dist: float = 0.2,
               trajectory_file: str = 'ase_opt.traj',
               log_file: str = 'ase_opt.log',
               **kwargs):
        
        ase_atoms = AseAtomsAdaptor.get_atoms(structure)

        ase_atoms.calc = DP(model=deepmd_model)

        dyn = BFGS(atoms=ase_atoms, logilfe = log_file, 
                   trajectory = trajectory_file, maxstep = max_dist)

        dyn.run(fmax=fmax)
        
        traj = Trajectory(trajectory_file)
        final_ase_atoms = traj[-1]
        
        final_pym_struct = AseAtomsAdaptor(atoms=final_ase_atoms)
        
        final_result = {
                    "structure": final_pym_struct.to_toolkit(),
                    "energy": final_ase_atoms.get_potential_energy(),
                    #"band_gap": result.band_gap,
                    #"is_gap_direct": result.is_gap_direct,
                    #"energy_fermi": result.energy_fermi,
                    #"conduction_band_minimum": result.conduction_band_minimum,
                    #"valence_band_maximum": result.valence_band_maximum,
                    "site_forces": final_ase_atoms.get_forces(),
                    #"lattice_stress": result.lattice_stress,
                }
        
        return final_result
                
        
