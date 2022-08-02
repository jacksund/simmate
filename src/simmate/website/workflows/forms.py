# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ValidationError

from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow

# TODO:
# class SubmitWorkflowYaml(forms.ModelForm):
#     pass


class SubmitWorkflow(forms.Form):

    # All workflows, regardless of their other parameters, will always have a
    # "labels" input. This is a list of labels to submit the workflow with.
    labels = forms.CharField(initial="WarWulf")

    def clean(self):
        # This method cleans multiple fields that depend on eachother.
        # See https://docs.djangoproject.com/en/4.0/ref/forms/validation/
        cleaned_data = super().clean()

        # For each of the fields in the file-or-json mapping, the user must
        # supply one of the two and NOT both. This for loop goes these fields
        # that require this and ensure this has been completed.
        actual_fields = self.base_fields.keys()
        for possible_field in INPUT_MAPPINGS["file-or-json"]:
            if f"{possible_field}_file" in actual_fields:
                file_input = cleaned_data.pop(f"{possible_field}_file", None)
                json_input = cleaned_data.pop(f"{possible_field}_json", None)

                if not file_input and not json_input:
                    raise ValidationError(
                        f"An input for {possible_field} is required. Please either "
                        "provide a file or json input for this parameter."
                    )
                elif file_input and json_input:
                    raise ValidationError(
                        f"Only one input for {possible_field} is allowed. Please either "
                        "provide a file or json input for this parameter -- not both."
                    )

                # lastly we want to remove these two fields and set the final
                # one to the parameter name (e.g. "structure_file" will be
                # changed to kwarg "structure")
                cleaned_data[possible_field] = file_input if file_input else json_input

        return cleaned_data

    def clean_structure_json(self, field_name: str = "structure_json"):

        # Grab what the user submitted
        structure_json = self.cleaned_data[field_name]

        if not structure_json:
            # This means not structure_file was provided and the user should
            # have supplied a structure_json instead.
            return

        try:
            structure = Structure.from_dynamic(structure_json)
        except:
            raise ValidationError("Failed to load the JSON input provided.")

        return structure

    def clean_structure_file(self, field_name: str = "structure_file"):

        # Grab what the user submitted
        structure_file = self.cleaned_data[field_name]

        # Make sure the file isn't too large
        if structure_file:
            # 5e6 is 5MB limit
            if structure_file.size > 5e6:
                raise ValidationError("File upload is too large (>5MB)")
        else:
            # This means not structure_file was provided and the user should
            # have supplied a structure_json instead.
            return

        # If we make it through the checks above, we can now convert the
        # text of the file into a pymatgen structure object
        structure_str = structure_file.read().decode("utf-8")

        # OPTIMIZE: is there a cleaner way to determine format?
        formats = ["cif", "poscar", "cssr", "json", "yaml", "xsf", "mcsqs"]
        for fmt in formats:
            try:
                structure = Structure.from_str(structure_str, fmt=fmt)
            except:
                structure = None

            # break the for-loop once structure is succesfully loaded
            if structure:
                break

        # ensure we loaded the structure successfully
        if not structure:
            raise ValidationError(
                f"Fail to read the file provided. Supported formats are... {formats}"
            )

        return structure

    def clean_structure_start_json(self):
        return self.clean_structure_json("supercell_start_json")

    def clean_structure_end_json(self):
        return self.clean_structure_json("supercell_end_json")

    def clean_migration_images_json(self):
        return self.clean_structure_json("migration_images_json")

    def clean_structure_start_file(self):
        return self.clean_structure_file("supercell_start_file")

    def clean_structure_end_file(self):
        return self.clean_structure_file("supercell_end_file")

    def clean_migration_images_file(self):
        return self.clean_structure_file("migration_images_file")

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

    @classmethod
    def from_workflow(cls, workflow: Workflow):

        # We keep a running dictionary of options for the form.
        form_fields = {}
        for parameter_name in workflow.parameter_names:

            is_required = parameter_name in workflow.parameter_names_required

            if parameter_name in INPUT_MAPPINGS["file-or-json"]:
                # Only one of these two inputs is required. I set required=False
                # for both, but I should check that one is given within this
                # class's "clean" method

                # Max length refers to the filename length, not its contents
                form_fields[f"{parameter_name}_file"] = forms.FileField(
                    max_length=100,
                    required=False,
                )
                form_fields[f"{parameter_name}_json"] = forms.JSONField(required=False)

            elif parameter_name in INPUT_MAPPINGS["string"]:
                form_fields[parameter_name] = forms.CharField(
                    max_length=100,
                    required=is_required,
                )

            elif parameter_name in INPUT_MAPPINGS["integer"]:
                form_fields[parameter_name] = forms.IntegerField(required=is_required)

            elif parameter_name in INPUT_MAPPINGS["float"]:
                form_fields[parameter_name] = forms.FloatField(required=is_required)

            elif parameter_name in INPUT_MAPPINGS["boolean"]:
                form_fields[parameter_name] = forms.BooleanField(required=is_required)

            elif parameter_name in INPUT_MAPPINGS["json"]:
                form_fields[parameter_name] = forms.JSONField(required=is_required)

            else:
                raise Exception(f"Unknown input type for parameter {parameter_name}")

        # once we have all the fields, we can dynamically create the new class.
        NewClass = type("SubmitWorkflowForm", tuple([cls]), form_fields)

        return NewClass


# TODO: is there a way to dynamically inpsect types so that I don't need this?
# I need a way to accept filters from custom workflows as well. How should
# I handle user-based parameters?
INPUT_MAPPINGS = {
    "json": [
        "source",
        "migration_hop",
    ],
    "file-or-json": [
        "structure",
        "supercell_start",
        "supercell_end",
        "migration_images",
    ],
    "string": [
        "directory",
        "directory_old",
        "directory_new",
        "command",
        "migrating_specie",
    ],
    "integer": [
        "nsteps",
        "diffusion_analysis_id",
        "migration_hop_id",
    ],
    "float": [
        "temperature_end",
        "temperature_start",
        "time_step",
    ],
    "boolean": [
        "copy_previous_directory",
        "pre_standardize_structure",
        "pre_sanitize_structure",
        "is_restart",
    ],
}
