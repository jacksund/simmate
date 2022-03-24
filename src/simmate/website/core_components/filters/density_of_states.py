# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.website.core_components.filters import Calculation, Structure
from simmate.database.base_data_types import (
    DensityofStates as DensityofStatesTable,
    DensityofStatesCalc as DensityofStatesCalcTable,
)


class DensityofStates(filters.FilterSet):
    class Meta:
        model = DensityofStatesTable
        fields = dict(
            band_gap=["range"],
            energy_fermi=["range"],
            conduction_band_minimum=["range"],
            valence_band_maximum=["range"],
        )


class DensityofStatesCalc(DensityofStates, Calculation, Structure):
    class Meta:
        model = DensityofStatesCalcTable
        fields = {
            **Structure.get_fields(),
            **DensityofStates.get_fields(),
            **Calculation.get_fields(),
        }
