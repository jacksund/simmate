# -*- coding: utf-8 -*-

"""
This module is experimental and subject to change.
"""


from simmate.database.base_data_types import (
    table_column,
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)


class Dynamics(Structure, Calculation):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    """Base Info"""

    temperature_start = table_column.IntegerField(blank=True, null=True)
    temperature_end = table_column.IntegerField(blank=True, null=True)
    time_step = table_column.FloatField(blank=True, null=True)
    nsteps = table_column.IntegerField(blank=True, null=True)

    """ Query-helper Info """
    # None

    """ Relationships """
    # structures --> gives list of all IonicSteps


class IonicStep(Structure, Thermodynamics, Forces):
    class Meta:
        abstract = True
        app_label = "local_calculations"

    base_info = (
        ["number"] + Structure.base_info + Thermodynamics.base_info + Forces.base_info
    )
    """
    The base information for this database table. All other columns can be calculated
    using the columns in this list.
    """

    """Base Info"""
    # This is ionic step number for the given relaxation. This starts counting from 0.
    number = table_column.IntegerField()

    # Options output from Vasprun.as_dict
    # e_0_energy
    # e_fr_energy
    # e_wo_entrp
    # electronic_steps
    # forces
    # kinetic
    # lattice kinetic
    # nosekinetic
    # nosepot
    # stress
    # structure
    # total

    """ Query-helper Info """

    # note, temp can be inferred from temperature_start/end and nsteps
    # also note that some steps may not be at equilibrium temp (e.g. the 1st 100 steps of a run)
    temperature = table_column.FloatField(blank=True, null=True)

    """ Relationships """
    # each of these will map to a Dynamics, so you should typically access this
    # data through that class. The exception to this is when you want all ionic
    # steps accross many relaxations for a machine learning input.
    # These relationship can be found via...
    #   dynamics
