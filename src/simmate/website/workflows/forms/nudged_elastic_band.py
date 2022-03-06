# -*- coding: utf-8 -*-

from django import forms

from simmate.website.workflows.forms import Structure
from simmate.database.base_data_types.nudged_elastic_band import (
    DiffusionAnalysis as DiffusionAnalysisTable,
    MigrationHop as MigrationHopTable,
    MigrationImage as MigrationImageTable,
)


class DiffusionAnalysis(forms.ModelForm):
    class Meta:
        model = DiffusionAnalysisTable
        fields = "__all__"
        exclude = []


class MigrationHop(forms.ModelForm):
    class Meta:
        model = MigrationHopTable
        fields = "__all__"
        exclude = ["index_start", "index_end"]


class MigrationImage(forms.ModelForm):
    class Meta:
        model = MigrationImageTable
        fields = "__all__"
        exclude = Structure.Meta.exclude
