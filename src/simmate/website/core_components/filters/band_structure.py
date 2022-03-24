# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.website.core_components.filters import Calculation, Structure
from simmate.database.base_data_types import (
    BandStructure as BandStructureTable,
    BandStructureCalc as BandStructureCalcTable,
)


class BandStructure(filters.FilterSet):
    class Meta:
        model = BandStructureTable
        fields = dict(
            nbands=["range"],
            band_gap=["range"],
            band_gap_direct=["range"],
            is_gap_direct=["exact"],
            energy_fermi=["range"],
            conduction_band_minimum=["range"],
            valence_band_maximum=["range"],
            is_metal=["exact"],
        )


class BandStructureCalc(BandStructure, Calculation, Structure):
    class Meta:
        model = BandStructureCalcTable
        fields = {
            **Structure.get_fields(),
            **BandStructure.get_fields(),
            **Calculation.get_fields(),
        }
