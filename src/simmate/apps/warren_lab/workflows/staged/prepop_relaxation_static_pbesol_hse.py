# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.relaxation.pbesol import (
    Relaxation__Vasp__WarrenLabPbesol,
)
from simmate.engine import StagedWorkflow

# We want to run a PBE relaxation followed by an HSE static energy calculation.
# Copying the WAVECAR will make this much faster, but this requires that a
# WAVECAR exists. However, we generally don't want all relaxation calculations
# to save the WAVECAR so we make a custom workflow here.
class Relaxation__Vasp__WarrenLabPbesolWithWavecar(Relaxation__Vasp__WarrenLabPbesol):
    """
    This workflow is the same as the typical PBEsol relaxation but with the added
    tag in the INCAR for writing the WAVECAR. This is intended to be used with
    nested workflows to increase the speed of the static energy calculation
    """

    _incar_updates = dict(LWAVE=True)


class StagedCalculation__Vasp__WarrenLabRelaxationStaticPbeHse(StagedWorkflow):
    """
    Runs a PBEsol quality structure relaxation, an HSE quality static energy
    calculation.This method will also write the ELFCAR and CHGCAR files
    necessary for population analysis (i.e. oxidation state and electron count)
    """
    
    subworkflow_names = [
        "relaxation.vasp.warren-lab-pbesol-with-wavecar",
        "static-energy.vasp.warren-lab-prebadelf-hse",    
        ]
    files_to_copy = ["WAVECAR"]
    # We use pbesol as our default relaxation functional because it doesn't take
    # much more time than pbe and is considered to be more accurate for solids
    # (Phys. Rev. Lett. 102, 039902 (2009))
