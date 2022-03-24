# -*- coding: utf-8 -*-

from simmate.website.core_components.filters import (
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)
from simmate.database.base_data_types import StaticEnergy as StaticEnergyTable


class StaticEnergy(
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
):
    class Meta:
        model = StaticEnergyTable
        fields = dict(
            band_gap=["range"],
            is_gap_direct=["exact"],
            energy_fermi=["range"],
            conduction_band_minimum=["range"],
            valence_band_maximum=["range"],
            **Structure.get_fields(),
            **Forces.get_fields(),
            **Thermodynamics.get_fields(),
            **Calculation.get_fields(),
        )
