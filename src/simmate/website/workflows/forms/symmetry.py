# -*- coding: utf-8 -*-

from django import forms

from simmate.database.base_data_types import Spacegroup as SpacegroupTable


class Spacegroup(forms.ModelForm):
    class Meta:
        model = SpacegroupTable
        fields = "__all__"
        exclude = ["density_of_states_data"]
