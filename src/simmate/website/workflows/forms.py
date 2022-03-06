# -*- coding: utf-8 -*-

from django import forms

from simmate.toolkit import Structure
from simmate.workflows.static_energy import mit_workflow
from simmate.utilities import get_chemical_subsystems

# I'm still learning the best way to dynamically create the mix-in forms
# but there may be beneifits to using django-filter or alternatively django's
# class-based views to create these forms and views. I also avoid the use of
# forms.ModelForm for now because I want to slowly add query fields.


class StructureForm(forms.Form):
    class Meta:
        # model = ExampleModel
        fields = "__all__"
        exclude = ["source", "structure_string"]

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


class MITRelaxationForm(forms.Form):

    # Max length refers to the filename length, not its contents
    structure_file = forms.FileField(max_length=100)

    # The vasp_command to submit with
    vasp_command = forms.CharField(initial="mpirun -n 4 vasp_std > vasp.out")

    # List of labels to submit the workflow with. Use commas to separate.
    labels = forms.CharField(initial="WarWulf")

    def clean_structure_file(self):
        # Grab what the user submitted
        structure_file = self.cleaned_data["structure_file"]

        # Make sure the file isn't too large
        if structure_file:
            # 5e6 is 5MB limit
            if structure_file.size > 5e6:
                raise Exception("File upload is too large (>5MB)")
        else:
            raise Exception("Couldn't read uploaded image")

        # If we make it through the checks above, we can now convert the
        # text of the file into a pymatgen structure object
        structure_str = structure_file.read().decode("utf-8")
        structure = Structure.from_str(structure_str, fmt="POSCAR")

        return structure

    def clean_labels(self):

        # Grab what the user submitted
        labels_str = self.cleaned_data["labels"]

        # convert the string to a list of labels.
        # For example...
        #   "WarWulf, LongLeaf, DogWood"
        #       converts to
        #   ['WarWulf', ' LongLeaf', ' DogWood']
        labels = labels_str.strip().split(",")

        return labels
