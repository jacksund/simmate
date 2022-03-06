# -*- coding: utf-8 -*-

from django import forms

from simmate.website.workflows.forms import (
    Structure,
    Forces,
    Thermodynamics,
    Calculation,
)
from simmate.database.base_data_types.relaxation import (
    Relaxation as RelaxationTable,
    IonicStep as IonicStepTable,
)


class Relaxation(forms.ModelForm):
    class Meta:
        model = RelaxationTable
        fields = "__all__"
        exclude = (
            ["structure_start", "structure_final"]
            + Structure.Meta.exclude
            + Calculation.Meta.exclude
        )


class IonicStep(forms.ModelForm):
    class Meta:
        model = IonicStepTable
        fields = "__all__"
        exclude = (
            Structure.Meta.exclude + Thermodynamics.Meta.exclude + Forces.Meta.exclude
        )
