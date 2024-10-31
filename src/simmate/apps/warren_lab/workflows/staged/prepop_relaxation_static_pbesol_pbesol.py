# -*- coding: utf-8 -*-

from simmate.engine import StagedWorkflow

class StagedCalculation__Vasp__WarrenLabRelaxationStaticPbePbe(StagedWorkflow):
    """
    Runs an PBEsol quality structure relaxation and PBEsol quality static energy
    calculation.This method will also write the ELFCAR and CHGCAR files necessary
    for population analysis (i.e. oxidation state and electron count)
    """
    
    subworkflow_names = [
        "relaxation.vasp.warren-lab-pbesol-with-wavecar",
        "static-energy.vasp.warren-lab-prebadelf-pbesol",    
        ]
    files_to_copy = ["WAVECAR"]
    # We use pbesol as our default relaxation functional because it doesn't take
    # much more time than pbe and is considered to be more accurate for solids
    # (Phys. Rev. Lett. 102, 039902 (2009))
