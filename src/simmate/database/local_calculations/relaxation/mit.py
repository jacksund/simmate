# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.local_calculations.relaxation.base import (
    IonicStepStructure,
    Relaxation,
)

# --------------------------------------------------------------------------------------

# All ionic steps of relaxations are stored in the same table. This means the
# start structure, end structure, and those structure in-between are stored
# together here.


class MITRelaxationStructure(IonicStepStructure):

    # All structures in this table come from relaxation calculations, where
    # there can be many structures (one for each ionic steps) linked to a
    # single relaxation
    relaxation = models.ForeignKey(
        "MITRelaxation",  # in quotes becuase this is defined below
        on_delete=models.CASCADE,
        related_name="structures",
    )

    class Meta:
        app_label = "local_calculations"


# --------------------------------------------------------------------------------------


class MITRelaxation(Relaxation):

    """Base Info"""

    # All the base information is contained with the parent classes

    """ Relationships """
    # the source structure for this calculation
    structure_start = models.OneToOneField(
        MITRelaxationStructure,
        on_delete=models.CASCADE,
        related_name="relaxations_as_start",
        blank=True,
        null=True,
    )

    # the final structure for this calculation
    structure_final = models.OneToOneField(
        MITRelaxationStructure,
        on_delete=models.CASCADE,
        related_name="relaxations_as_final",
        blank=True,
        null=True,
    )

    # all other structures are accessible through the "structures" field

    class Meta:
        app_label = "local_calculations"


# --------------------------------------------------------------------------------------
