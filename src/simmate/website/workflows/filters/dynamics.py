# -*- coding: utf-8 -*-

from simmate.website.workflows.filters import (
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)
from simmate.database.base_data_types.dynamics import (
    DynamicsRun as DynamicsRunTable,
    DynamicsIonicStep as DynamicsIonicStepTable,
)


class DynamicsRun(Structure, Calculation):
    class Meta:
        model = DynamicsRunTable
        fields = dict(
            temperature_start=["exact", "range"],
            temperature_end=["exact", "range"],
            time_step=["exact", "range"],
            nsteps=["exact", "range"],
            **Structure.get_fields(),
            **Calculation.get_fields(),
        )


class DynamicsIonicStep(Structure, Forces, Thermodynamics):
    class Meta:
        model = DynamicsIonicStepTable
        fields = dict(
            number=["exact", "range"],
            temperature=["exact", "range"],
            **Structure.get_fields(),
            **Thermodynamics.get_fields(),
            **Forces.get_fields(),
        )
