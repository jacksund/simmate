# -*- coding: utf-8 -*-

from django import forms
from simmate.website.workflows.forms import StructureForm


class ChemicalSystemForm(StructureForm):

    # Searching by Database Providers
    aflow = forms.BooleanField(required=False)
    cod = forms.BooleanField(required=False)
    jarvis = forms.BooleanField(required=False)
    materials_project = forms.BooleanField(required=False)
    simmate = forms.BooleanField(required=False)
    oqmd = forms.BooleanField(required=False)
