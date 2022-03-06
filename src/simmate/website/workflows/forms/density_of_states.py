# -*- coding: utf-8 -*-

from django import forms

from simmate.website.workflows.forms import Calculation, Structure
from simmate.database.base_data_types import (
    DensityofStates as DensityofStatesTable,
    DensityofStatesCalc as DensityofStatesCalcTable,
)


class DensityofStates(forms.ModelForm):
    class Meta:
        model = DensityofStatesTable
        fields = "__all__"
        exclude = ["density_of_states_data"]


class DensityofStatesCalc(forms.ModelForm):
    class Meta:
        model = DensityofStatesTable
        fields = "__all__"
        exclude = (
            Structure.Meta.exclude
            + DensityofStates.Meta.exclude
            + Calculation.Meta.exclude
        )
