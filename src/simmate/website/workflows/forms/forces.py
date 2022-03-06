# -*- coding: utf-8 -*-

from django import forms

from simmate.database.base_data_types import Forces as ForcesTable


class Forces(forms.ModelForm):
    class Meta:
        model = ForcesTable
        fields = "__all__"
        exclude = ["site_forces", "lattice_stress", "site_forces_norm"]
