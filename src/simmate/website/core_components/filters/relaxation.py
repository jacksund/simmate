# -*- coding: utf-8 -*-

from simmate.website.core_components.filters import (
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)
from simmate.database.base_data_types.relaxation import (
    Relaxation as RelaxationTable,
    IonicStep as IonicStepTable,
)


class Relaxation(Structure, Calculation):
    class Meta:
        model = RelaxationTable
        fields = dict(
            volume_change=["range"],
            band_gap=["exact", "range"],
            is_gap_direct=["exact"],
            energy_fermi=["range"],
            conduction_band_minimum=["range"],
            valence_band_maximum=["range"],
            **Structure.get_fields(),
            **Calculation.get_fields(),
        )


class IonicStep(Structure, Forces, Thermodynamics):
    class Meta:
        model = IonicStepTable
        fields = dict(
            **Structure.get_fields(),
            **Thermodynamics.get_fields(),
            **Forces.get_fields(),
        )
