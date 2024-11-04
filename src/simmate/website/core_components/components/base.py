# -*- coding: utf-8 -*-

from django.shortcuts import redirect
from django_unicorn.components import UnicornView

from simmate.database.base_data_types import DatabaseTable
from simmate.toolkit import Molecule, Structure


class DynamicFormComponent(UnicornView):
    """
    The abstract base class for dynamic front-end views.
    """

    template_name: str = None
    """
    The location of the template to use for this component
    """
    # TODO: Could there be a template that auto builds the form html? But this
    # might get messy and not be worth it.

    class Meta:
        javascript_exclude = (
            "table",
            "required_inputs",
            "ignore_on_update",
        )

    # -------------------------------------------------------------------------

    form_mode: str = None  # should be "create" or "update"

    def mount(self):
        view_name = self.request.resolver_match.url_name
        view_kwargs = self.request.resolver_match.kwargs
        # !!! I could set the self.table attr using these kwargs

        if view_name == "table-entry-new":
            self.form_mode = "create"
            self.mount_for_create()
        elif view_name == "table-entry-update":
            self.form_mode = "update"
            self.table_entry = self.table.objects.get(id=view_kwargs["table_entry_id"])
            self.mount_for_update()
        else:
            raise Exception(f"Unknown view type for dynamic form: {view_name}")

        self.mount_extra()

    def mount_extra(self):
        return  # default is there's nothing extra to do

    def mount_for_create(self):
        return  # default is there's nothing extra to do

    def mount_for_update(self):
        # set initial data using the database and applying its values to
        # the form fields.
        config = self.to_db_dict()
        for field in config:
            current_val = getattr(self.table_entry, field)
            setattr(self, field, current_val)

    # -------------------------------------------------------------------------

    def set_property(
        self,
        # BUG: for some reason, giving ": str" causes errors...?
        property_name: any,
        new_value: any,
        *args,
        **kwargs,
    ):
        # check if there is a special defined method for this property
        method_name = f"set_{property_name}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(new_value, *args, **kwargs)
        else:
            setattr(self, property_name, new_value)

    # -------------------------------------------------------------------------

    # Model creation and update utils

    table_entry: DatabaseTable = None  # initialized object
    table: DatabaseTable = None  # class object

    def to_db_dict(self) -> dict:
        return self._get_default_db_dict()

    def _get_default_db_dict(self, load_toolkits: bool = True) -> dict:
        # I don't like calling super() in overwrites for `to_db_dict`, so
        # I use this method instead.

        # By default, we say the form maps to columns of the model with same name.
        # We also check for direct relations, which would end in "_id"
        # (e.g. 'created_by_id' for users where col is technically 'created_by')
        form_attrs = self._attribute_names_cache
        table_cols = self.table.get_column_names()
        matching_fields = [
            attr
            for attr in form_attrs
            if attr in table_cols or (attr.endswith("_id") and attr[:-3] in table_cols)
        ]

        config = {}
        for form_attr in matching_fields:
            current_val = getattr(self, form_attr)
            config[form_attr] = current_val

            # special data types and common field names. Note, variations
            # of this should be handled by overriding the `to_db_dict`
            if load_toolkits and current_val is not None:
                if form_attr == "molecule":
                    config["molecule_original"] = current_val
                    config["molecule"] = Molecule.from_dynamic(current_val)
                elif form_attr == "structure":
                    config["structure_original"] = current_val
                    config["structure"] = Structure.from_dynamic(current_val)

        return config

    # -------------------------------------------------------------------------

    # Basic form validation utils

    required_inputs: list[str] = []
    """
    For submission forms, these are the list of attributes that must be
    completed, otherwise the form will not submit.
    """

    def check_required_inputs(self):
        # Check that all basic inputs are filled out
        for input_name in self.required_inputs:
            input_value = getattr(self, input_name)
            if not input_value:
                message = f"'{input_name}' is a required input."
                self.form_errors.append(message)

    # -------------------------------------------------------------------------

    # Validation Hooks

    form_errors = []

    def check_form(self) -> bool:
        # reset errors for this new check
        self.form_errors = []

        self.check_required_inputs()
        self.check_form_hook()

        return True if not self.form_errors else False

    def check_form_hook(self) -> bool:
        return True  # default is there's nothing extra to check

    # -------------------------------------------------------------------------

    # Submission Hooks

    ignore_on_update: list[str] = []

    def submit_form(self):

        # check form is valid
        if not self.check_form():
            return

        if self.form_mode == "create":
            self.unmount_for_create()
        elif self.form_mode == "update":
            self.unmount_for_update()
        else:
            raise Exception(f"Unknown form_mode for dynamic form: {self.form_mode}")

        self.presave_to_db()
        self.save_to_db()
        self.postsave_to_db()

        return self.get_submission_redirect()

    def unmount_for_create(self):
        self.table_entry = self.table.from_toolkit(**self.to_db_dict())

    def unmount_for_update(self):
        # set initial data using the form fields and applying its values to
        # the table entry (this is the reverse of mount_for_update)
        config = self.to_db_dict()
        for field in config:
            if not hasattr(self, field) or field in self.ignore_on_update:
                # skip things like "molecule" and "molecule_original" that are
                # present for creation but should be ignored here
                continue
            current_val = getattr(self, field)
            setattr(self.table_entry, field, current_val)

    def presave_to_db(self):
        return  # default is there's nothing extra to do

    def save_to_db(self):
        self.table_entry.save()

    def postsave_to_db(self):
        return  # default is there's nothing extra to do

    def get_submission_redirect(self):
        return redirect(
            "data_explorer:table-entry",
            self.table.table_name,
            self.table_entry.id,
        )
        # TODO: give option to return to the table view...?
        # return redirect(
        #     "data_explorer:table",
        #     self.table.table_name,
        # )

    # BUG: race condition if user double-clicks button, triggering 2 calls to
    # the 'submit_form' method, which can create multiple instances of the
    # same entry.
    # Soluton 1:
    #   https://stackoverflow.com/questions/16715075/
    # Solution 2:
    # to prevent duplicates from being made, we need this to be update_or_create
    # inchi_key = config["molecule"].to_inchi_key()
    # self.table.objects.update_or_create(
    #     inchi_key=inchi_key,
    #     defaults=self.table.from_toolkit(
    #         as_dict=True,
    #         **self.to_db_dict(),
    #     ),
    # )

    # -------------------------------------------------------------------------
