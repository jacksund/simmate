# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.website.workflows.filters import Calculation, Structure
from simmate.database.base_data_types import (
    BandStructure as BandStructureTable,
    BandStructureCalc as BandStructureCalcTable,
)


class BandStructure(filters.FilterSet):
    class Meta:
        model = BandStructureTable
        fields = dict(
            nbands=["exact", "range"],
            band_gap=["exact", "range"],
            band_gap_direct=["exact", "range"],
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
