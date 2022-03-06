# -*- coding: utf-8 -*-

from django import forms

from simmate.database.base_data_types import Thermodynamics as ThermodynamicsTable


class Thermodynamics(forms.ModelForm):
    class Meta:
        model = ThermodynamicsTable
        fields = "__all__"
        exclude = ["decomposes_to"]
