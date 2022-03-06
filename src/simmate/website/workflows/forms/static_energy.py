# -*- coding: utf-8 -*-

from django import forms

from simmate.website.workflows.forms import (
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)
from simmate.database.base_data_types import StaticEnergy as StaticEnergyTable


class StaticEnergy(forms.ModelForm):
    class Meta:
        model = StaticEnergyTable
        fields = "__all__"
        exclude = (
            Structure.Meta.exclude
            + Forces.Meta.exclude
            + Thermodynamics.Meta.exclude
            + Calculation.Meta.exclude
        )
