# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.database.base_data_types import Calculation as CalculationTable


class Calculation(filters.FilterSet):
    class Meta:
        model = CalculationTable
        fields = dict(
            directory=["exact"],
            prefect_flow_run_id=["exact"],
            created_at=["range"],
            updated_at=["range"],
        )
