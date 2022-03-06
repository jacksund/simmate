# -*- coding: utf-8 -*-

from django import forms

from simmate.website.workflows.forms import (
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)
from simmate.database.base_data_types.dynamics import (
    DynamicsRun as DynamicsRunTable,
    DynamicsIonicStep as DynamicsIonicStepTable,
)


class DynamicsRun(forms.ModelForm):
    class Meta:
        model = DynamicsRunTable
        fields = "__all__"
        exclude = Structure.Meta.exclude + Calculation.Meta.exclude


class DynamicsIonicStep(forms.ModelForm):
    class Meta:
        model = DynamicsIonicStepTable
        fields = "__all__"
        exclude = (
            Structure.Meta.exclude + Thermodynamics.Meta.exclude + Forces.Meta.exclude
        )
