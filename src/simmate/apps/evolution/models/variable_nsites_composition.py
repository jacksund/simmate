# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Calculation, table_column


class VariableNsitesCompositionSearch(Calculation):
    class Meta:
        app_label = "workflows"

    # OPTIMIZE: This is really just a copy/paste of the fixed-composition
    # workflow, where we aren't using the table directly in the search and
    # skips making steadystate_source table entries. It simply stores input
    # parameters.
    composition = table_column.CharField(max_length=50, null=True, blank=True)
    subworkflow_name = table_column.CharField(max_length=200, null=True, blank=True)
    subworkflow_kwargs = table_column.JSONField(default=dict, null=True, blank=True)
    fitness_field = table_column.CharField(max_length=200, null=True, blank=True)
    nfirst_generation = table_column.IntegerField(null=True, blank=True)
    nsteadystate = table_column.IntegerField(null=True, blank=True)
    selector_name = table_column.CharField(max_length=200, null=True, blank=True)
    selector_kwargs = table_column.JSONField(default=dict, null=True, blank=True)
    validator_name = table_column.CharField(max_length=200, null=True, blank=True)
    validator_kwargs = table_column.JSONField(default=dict, null=True, blank=True)
    stop_conditions = table_column.JSONField(default=dict, null=True, blank=True)
    sleep_step = table_column.FloatField(null=True, blank=True)
    
