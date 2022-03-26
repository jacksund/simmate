# -*- coding: utf-8 -*-

from django import forms

from simmate.utilities import get_chemical_subsystems

# NOTE TO DEV: This form is a special case where we are searching MANY tables
# for information -- so it is therefore not a ModelForm and cannot use
# our mix-ins. I need to think of the best way to leverage these mix-ins without
# creating this form from scratch. For now, this form is effectively a copy/paste
# of `from simmate.website.core_components.filters import Structure`.


class ChemicalSystemForm(forms.Form):

    include_subsystems = forms.BooleanField(
        label="Include Subsytems",
        required=False,
    )
    """
    Whether to include subsystems of the given `chemical_system`. For example,
    the subsystems of Y-C-F would be Y, C, F, Y-C, Y-F, etc..
    """
    # Note: this attribute must be positioned BEFORE chemical_system to ensure
    # it is present in self.cleaned_data before chemical_system is accessed.

    # include_suprasystems = forms.BooleanField(label="Include Subsytems", required=False)
    # TODO: Supra-systems would include all the elements listed AND more. For example,
    # searching Y-C-F would also return Y-C-F-Br, Y-Sc-C-F, etc.

    chemical_system = forms.CharField(
        label="Chemical System",
        max_length=20,
        required=False,
    )
    """
    The chemical system of the structure (e.g. "Y-C-F" or "Na-Cl")
    """

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
