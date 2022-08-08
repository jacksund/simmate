# -*- coding: utf-8 -*-


from simmate.database.base_data_types import StaticEnergy, table_column


class PopulationAnalysis(StaticEnergy):
    """
    This table combines results from a static energy calculation and the follow-up
    oxidation analysis on the charge density.
    """

    class Meta:
        app_label = "workflows"

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states based on some analysis. This is 
    given back as a list of float values in the same order as sites in the
    source structure.
    """
