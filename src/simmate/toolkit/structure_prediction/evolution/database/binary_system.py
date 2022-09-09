# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Calculation, table_column


class BinarySystemSearch(Calculation):
    class Meta:
        app_label = "workflows"

    chemical_system = table_column.CharField(max_length=10, null=True, blank=True)
    subworkflow_name = table_column.CharField(max_length=200, null=True, blank=True)
    subworkflow_kwargs = table_column.JSONField(default=dict, null=True, blank=True)
    max_atoms = table_column.IntegerField(null=True, blank=True)
    max_stoich_factor = table_column.IntegerField(null=True, blank=True)
    singleshot_sources = table_column.JSONField(default=list, null=True, blank=True)
