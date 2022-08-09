# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.database.base_data_types import Calculation as CalculationTable


class Calculation(filters.FilterSet):
    class Meta:
        model = CalculationTable
        fields = dict(
            directory=["exact"],
            run_id=["exact"],
            created_at=["range"],
            updated_at=["range"],
        )
