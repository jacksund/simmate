# -*- coding: utf-8 -*-

from simmate.database.base_data_types import StaticEnergy, table_column


class MatprojBaderAnalysis(StaticEnergy):
    """
    This table combines results from a static energy calculation and the follow-up
    bader analysis on the charge density.
    """

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states based on Bader analysis. This is 
    given back as a list of float values in the same order as sites in the
    source structure.
    """


# THIS IS A COPY/PASTE FROM ABOVE-- I need to condense these and add a new base_type
class MatprojBaderELFAnalysis(StaticEnergy):
    """
    This table combines results from a static energy calculation and the follow-up
    bader analysis on the charge density.
    """

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states based on Bader analysis. This is 
    given back as a list of float values in the same order as sites in the
    source structure.
    """


class MatprojELF(StaticEnergy):
    pass
