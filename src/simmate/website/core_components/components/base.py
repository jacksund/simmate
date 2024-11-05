# -*- coding: utf-8 -*-

import json

from django.shortcuts import redirect
from django_unicorn.components import UnicornView

from simmate.database.base_data_types import DatabaseTable
from simmate.toolkit import Molecule, Structure
from simmate.website.utilities import parse_request_get


class DynamicFormComponent(UnicornView):
    """
    The abstract base class for dynamic front-end views.
    """

    class Meta:
        javascript_exclude = (
            # "template_name",  # included by parent class
            "table",
            "required_inputs",
            "ignore_on_update",
            "update_many_inputs",
        )

    template_name: str = None
    """
    The location of the template to use for this component
    """
    # TODO: Could there be a template that auto builds the form html? But this
    # might get messy and not be worth it.

    table: DatabaseTable = None  # class object
    """
    The database table that this form is intended to create/update rows for
    """

    required_inputs: list[str] = []
    """
    For update and create form modes, these are the list of attributes that must
    be completed, otherwise the form will not submit.
    """

    ignore_on_update: list[str] = []
    """
    List of columns/fields to ignore when the form_mode = "update"
    """

    update_many_inputs: list[str] = []
    """
    List of columns/fields to allow when the form_mode = "update-many"
    """

    n_ids_to_update_max: int = 25
    """
    The max number of entries that can be editted at one time when
    form_mode = "update-many"
    """

    # -------------------------------------------------------------------------

    # These are dynamic and part of the form, so they are included in the AJAX json

    parent_url: str = None
    """
    The original URL where this form is embeded. This attr is primarily for
    the data "table" view where there are many forms, and after the form is
    submitted, we'd want to refresh the parent url (including any GET kwargs)
    """

    redirect_mode: str = "table_entry"
    """
    Controls which page the user is redirected to after form submission. 
    Options are "table_entry", "table", and "parent_url"
    """

    table_entry: DatabaseTable = None  # initialized object
    """
    If form_mode is "create" or "update", this is the single table entry that
    is being created or updated. This is set dynamically by the class.
    """

    form_mode: str = None
    """
    The mode the form is currently in. Options are "create", "update", 
    "update-many", and "create-many".
    
    In some cases this does not need to be set because it can be inferred from
    the parent_url
    """

    is_update_many_confirmed: bool = False
    """
    Whether the user accepted the warning that there is no undo button
    """

    entry_ids_to_update: list = []
    """
    The list of selected ids that will be updated. Only applies when the
    form_mode = "update-many"
    """

    # -------------------------------------------------------------------------

    def mount(self):
        # needed for resubmission
        self.parent_url = self.request.get_full_path()

        view_name = self.request.resolver_match.url_name
        view_kwargs = self.request.resolver_match.kwargs
        # !!! I could set the self.table attr using these kwargs

        # Dynamically determine form_mode using the view name if it is not
        # specified in the html template directly
        if not self.form_mode:
            if view_name == "table-entry-new":
                self.form_mode = "create"
            elif view_name == "table-entry-update":
                self.form_mode = "update"
            else:
                raise Exception(f"Unknown view type for dynamic form: {view_name}")

        # Call the corresponding mount() method based on our mode
        if self.form_mode == "create":
            self.mount_for_create()
        elif self.form_mode == "update":
            self.table_entry = self.table.objects.get(id=view_kwargs["table_entry_id"])
            self.mount_for_update()
        elif self.form_mode == "update-many":
            self.mount_for_update_many()
        else:
            raise Exception(f"Unknown view type for dynamic form: {view_name}")

        self.mount_get_kwargs()
        self.mount_extra()

    def mount_get_kwargs(self):
        get_kwargs = parse_request_get(self.request)
        for field, value in get_kwargs.items():
            setattr(self, field, value)

    def mount_for_create(self):
        return  # default is there's nothing extra to do

    def mount_for_update(self):
        # set initial data using the database and applying its values to
        # the form fields.
        config = self.to_db_dict()
        for field in config:
            current_val = getattr(self.table_entry, field)
            setattr(self, field, current_val)

    def mount_for_update_many(self):
        # default is we want everything to be set to None, which includes
        # overriding default values
        for field in self.update_many_inputs:
            setattr(self, field, None)

    def mount_extra(self):
        return  # default is there's nothing extra to do

    # -------------------------------------------------------------------------

    def unmount(self):
        if self.form_mode == "create":
            self.unmount_for_create()
        elif self.form_mode == "update":
            self.unmount_for_update()
        elif self.form_mode == "update-many":
            self.unmount_for_update_many()
        else:
            raise Exception(f"Unknown form_mode for dynamic form: {self.form_mode}")

        self.unmount_extra()

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

    def unmount_for_update_many(self):
        config = self.to_db_dict()
        self.final_updates = {
            field: value
            for value, field in config.items()
            if not hasattr(self, field)
            or field in self.ignore_on_update
            or field not in self.update_many_inputs
        }

    def unmount_extra(self):
        return  # default is there's nothing extra to do

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
            if load_toolkits and current_val not in [None, "None", "NONE", ""]:
                if form_attr == "molecule":
                    config["molecule_original"] = current_val
                    config["molecule"] = Molecule.from_dynamic(current_val)
                elif form_attr == "structure":
                    config["structure_original"] = current_val
                    config["structure"] = Structure.from_dynamic(current_val)
        return config

    # -------------------------------------------------------------------------

    # Basic form validation utils

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

        if self.form_mode in ["create", "update"]:
            self.check_required_inputs()
        elif self.form_mode == "update-many":
            self.check_max_update_many()

        self.check_form_hook()

        return True if not self.form_errors else False

    def check_form_hook(self) -> bool:
        return True  # default is there's nothing extra to check

    # -------------------------------------------------------------------------

    # Extra utils for form_mode="update-many"

    def check_max_update_many(self):
        if len(self.entry_ids_to_update) > self.n_ids_to_update_max:
            message = f"You are only allowed to update a maximum of '{self.n_ids_to_update_max}' at a time."
            self.form_errors.append(message)

    def confirm_update_many(self, select_form_data):
        # Example of how the data will look:
        # {
        #     "1": "on",
        #     "2": "on",
        #     "4": "on",
        #     "csrfmiddlewaretoken": "LTJaJf5gz6fUKUZaN0p6gMyVnLQGM7LGjPRVohe3pVgR5M0UpepNokgePN3pQ4dI"
        # }
        data = json.loads(select_form_data)
        data.pop("csrfmiddlewaretoken", None)
        data.pop("cortevatarget_select_all", None)
        self.entry_ids_to_update = [int(key) for key, value in data.items()]

        if self.entry_ids_to_update:
            self.is_update_many_confirmed = True

    # -------------------------------------------------------------------------

    # Submission Hooks

    def submit_form(self):

        # check form is valid
        if not self.check_form():
            return

        # then call series of final hooks
        self.unmount()
        self.presave_to_db()
        self.save_to_db()
        self.postsave_to_db()

        # and provide final url
        return self.get_submission_redirect()

    def presave_to_db(self):
        return  # default is there's nothing extra to do

    def save_to_db(self):
        if self.form_mode in ["create", "update"]:
            self.table_entry.save()
        elif self.form_mode == "update-many":

            # Special cases! Comments should be appended so nothing is lost

            self.table.objects.filter(id__in=self.entry_ids_to_update).update(
                **self.final_updates
            )

    def postsave_to_db(self):
        return  # default is there's nothing extra to do

    def get_submission_redirect(self):
        if self.redirect_mode == "table_entry":
            return redirect(
                "data_explorer:table-entry",
                self.table.table_name,
                self.table_entry.id,
            )
        elif self.redirect_mode == "table":
            return redirect(
                "data_explorer:table",
                self.table.table_name,
            )
        elif self.redirect_mode == "parent_url":
            # Refresh current page (which could be the table view + a query)
            return redirect(self.parent_url)
        else:
            raise Exception(
                f"Unknown redirect_mode for dynamic form: {self.redirect_mode}"
            )

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
