# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.structure import Structure
from simmate.database.calculation import Calculation

class Relaxation(Calculation):
    
    bandgap
    conduction_band_minimum
    valence_band_maximum
    is_gap_direct
    energy_fermi
    
    final_energy
    final_energy_per_atom
    
    ionic_steps
        e_0_energy
        e_fr_energy
        e_wo_entrp
        electronic_steps
        forces
        stress
        structure
