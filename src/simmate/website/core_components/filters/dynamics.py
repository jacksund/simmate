# -*- coding: utf-8 -*-

from simmate.database.base_data_types.dynamics import (
    DynamicsIonicStep as DynamicsIonicStepTable,
)
from simmate.database.base_data_types.dynamics import DynamicsRun as DynamicsRunTable
from simmate.website.core_components.filters import (
    Calculation,
    Forces,
    Structure,
    Thermodynamics,
)


class DynamicsRun(Structure, Calculation):
    class Meta:
        model = DynamicsRunTable
        fields = dict(
            temperature_start=["range"],
            temperature_end=["range"],
            time_step=["range"],
            nsteps=["range"],
            **Structure.get_fields(),
            **Calculation.get_fields(),
        )


class DynamicsIonicStep(Structure, Forces, Thermodynamics):
    class Meta:
        model = DynamicsIonicStepTable
        fields = dict(
            number=["range"],
            temperature=["range"],
            **Structure.get_fields(),
            **Thermodynamics.get_fields(),
            **Forces.get_fields(),
        )
