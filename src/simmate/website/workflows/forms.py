# -*- coding: utf-8 -*-

from django import forms

from simmate.toolkit import Structure


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
