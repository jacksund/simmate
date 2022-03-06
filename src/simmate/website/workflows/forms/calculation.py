# -*- coding: utf-8 -*-

from django import forms

from simmate.database.base_data_types import Calculation as CalculationTable


class Calculation(forms.ModelForm):
    class Meta:
        model = CalculationTable
        fields = "__all__"
        exclude = ["corrections"]
