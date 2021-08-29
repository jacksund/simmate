# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.structure import Structure
from simmate.database.calculation import Calculation


# --------------------------------------------------------------------------------------

# Initial and Final Structure of the calculation get their own table


class MITRelaxationInitialStructure(Structure):
    class Meta:
        app_label = "local_calculations"


class MITRelaxationFinalStructure(Structure):
    
    class Meta:
        app_label = "local_calculations"


# --------------------------------------------------------------------------------------


class MITRelaxation(Calculation):

    """Base Info"""

    # Informated extracted from the calculation
    final_energy = models.FloatField(blank=True, null=True)
    
    # TODO:
    # energy_per_atom = models.FloatField(blank=True, null=True)
    # bandgap = models.FloatField(blank=True, null=True)
    # forces = models.JSONField(blank=True, null=True)
    # stress = models.JSONField(blank=True, null=True)
    
    """ Relationships """
    # Map to the input and output structures for the calc
    structure_initial = models.OneToOneField(
        MITRelaxationInitialStructure, on_delete=models.CASCADE,
    )
    structure_final = models.OneToOneField(
        MITRelaxationFinalStructure, on_delete=models.CASCADE, blank=True, null=True,
    )

    class Meta:
        app_label = "local_calculations"
