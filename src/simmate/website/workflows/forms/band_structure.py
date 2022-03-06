# -*- coding: utf-8 -*-

from django import forms

from simmate.website.workflows.forms import Calculation, Structure
from simmate.database.base_data_types import (
    BandStructure as BandStructureTable,
    BandStructureCalc as BandStructureCalcTable,
)


class BandStructure(forms.ModelForm):
    class Meta:
        model = BandStructureTable
        fields = "__all__"
        exclude = ["band_structure_data"]


class BandStructureCalc(forms.ModelForm):
    class Meta:
        model = BandStructureCalcTable
        fields = "__all__"
        exclude = (
            Structure.Meta.exclude
            + BandStructure.Meta.exclude
            + Calculation.Meta.exclude
        )
