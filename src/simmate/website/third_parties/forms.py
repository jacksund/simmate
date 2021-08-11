# -*- coding: utf-8 -*-

from django import forms

from simmate.utilities import get_chemical_subsystems


class ChemicalSystemForm(forms.Form):

    # This is the most basic form for querying data, which only takes
    # the chemical system. This way users can quickly query with a composition
    # such as "Y-C-F". We also ask if they want the subsystem too. For example,
    # Y-C-F would also include Y, C, F, Y-C, Y-F, etc. in the search results.

    # We want a lot of control here and this form will be applied to multiple
    # tables/models, so we don't use django-filter here.

    # Searching by Chemical System
    include_subsystems = forms.BooleanField(label="Include Subsytems", required=False)
    chemical_system = forms.CharField(label="Chemical System", max_length=20)

    # Searching by Database Providers
    aflow = forms.BooleanField(required=False)
    cod = forms.BooleanField(required=False)
    jarvis = forms.BooleanField(required=False)
    materials_project = forms.BooleanField(required=False)
    simmate = forms.BooleanField(required=False)
    oqmd = forms.BooleanField(required=False)

    def clean_chemical_system(self):

        # Our database expects the chemical system to be given in alphabetical
        # order, but we don't want users to recieve errors when they search for
        # "Y-C-F" instead of "C-F-Y". Therefore, we fix that for them here! We
        # also check if the user wants the chemical subsystems included.

        # Grab what the user submitted
        chemical_system = self.cleaned_data["chemical_system"]

        # TODO:
        # Make sure that the chemical system is made of valid elements and
        # separated by hyphens

        # check if the user wants subsystems included (This will be True or False)
        if self.cleaned_data["include_subsystems"]:
            systems_cleaned = get_chemical_subsystems(chemical_system)

        # otherwise just clean the single system
        else:
            # Convert the system to a list of elements
            systems_cleaned = chemical_system.split("-")
            # now recombine the list back into alphabetical order
            systems_cleaned = ["-".join(sorted(systems_cleaned))]
            # NOTE: we call this "systems_cleaned" and put it in a list so
            # that our other methods don't have to deal with multiple cases
            # when running a django filter.

        # now return the cleaned value. Note that this is now a list of
        # chemical systems, where all elements are in alphabetical order.
        return systems_cleaned
