# -*- coding: utf-8 -*-

import json
import urllib

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
            "n_ids_to_update_max",
            "page_size_options",
            "order_by_options",
        )

    template_name: str = None
    """
    The location of the template to use for this component
    """
    # TODO: Could there be a template that auto builds the form html? But this
    # might get messy and not be worth it.

    form_mode: str = None
    """
    The mode the form is currently in. Options are "create", "update", 
    "update-many", "create-many", and "search".
    
    In some cases this does not need to be set because it can be inferred from
    the parent_url
    """

    table: DatabaseTable = None  # class object
    """
    The database table that this form is intended to create/update rows for
    """

    table_entry: DatabaseTable = None  # initialized object
    """
    If form_mode is "create" or "update", this is the single table entry that
    is being created or updated. This is set dynamically by the class.
    """

    # -------------------------------------------------------------------------

    # To help with page redirects after submission

    redirect_mode: str = "table_entry"
    """
    Controls which page the user is redirected to after form submission. 
    Options are "table_entry", "table", and "refresh"
    """

    parent_url: str = None
    """
    The original URL where this form is embeded. This attr is primarily for
    the data "table" view where there are many forms, and after the form is
    submitted, we'd want to refresh the parent url (including any GET kwargs)
    """

    # -------------------------------------------------------------------------

    # for form_mode "create" and "update"

    required_inputs: list[str] = []
    """
    For update and create form modes, these are the list of attributes that must
    be completed, otherwise the form will not submit.
    """

    # -------------------------------------------------------------------------

    # for form_mode "update-many"

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

    # for form_mode "search"

    # assumed filters from DatabaseTable
    id__in = None

    page_size = None
    page_size_options = (
        (25, "25"),
        (50, "50"),
        (100, "100"),
    )

    order_by = None
    reverse_order_by = False

    @property
    def order_by_options(self):
        # reformat into tuple of (value, display)
        return [(col, col) for col in self.table.get_column_names()]

    def set_order_by(self, value):
        if value.startswith("-"):
            self.order_by = value[1:]
            self.reverse_order_by = True
        else:
            self.order_by = value
            self.reverse_order_by = False

    search_inputs = [
        "id__in",
        "page_size",
        "order_by",
        # "reverse_order_by",
    ]

    # -------------------------------------------------------------------------

    def mount(self):

        view_name = self.request.resolver_match.url_name

        # Dynamically determine form_mode using the view name if it is not
        # specified in the html template directly
        if not self.form_mode:
            if view_name == "table-entry-new":
                self.form_mode = "create"
            elif view_name == "table-entry-update":
                self.form_mode = "update"
            elif view_name == "table-entry-update-many":
                self.form_mode = "update-many"
            elif view_name == "table-entry-new-many":
                self.form_mode = "create-many"
            elif view_name == "table-entry-search":
                self.form_mode = "search"
            else:
                raise Exception(f"Unknown view type for dynamic form: {view_name}")

        # check that editting is actually allowed
        if not self.table.html_enable_edit_forms and self.form_mode in [
            "create",
            "update",
            "update-many",
            "create-many",
        ]:
            return Exception("Denied permissions to create/update data for this table.")

        # Call the corresponding mount() method based on our mode
        if self.form_mode == "create":
            self.mount_for_create()
        elif self.form_mode == "create-many":
            self.mount_for_create_many()
        elif self.form_mode == "update":
            self.mount_for_update()
        elif self.form_mode == "update-many":
            self.mount_for_update_many()
        elif self.form_mode == "search":
            self.mount_for_search()
        else:
            raise Exception(f"Unknown form_mode is set: {self.form_mode}")

        self.mount_url_info()
        self.mount_extra()

    def mount_url_info(self):
        # grab parent url for resubmission. We include GET params unless the
        # mode is search, in which case we only want the base path.
        self.parent_url = (
            self.request.path
            if self.form_mode == "search"
            else self.request.get_full_path()
        )
        # and then GET params
        get_kwargs = parse_request_get(self.request)
        for field, value in get_kwargs.items():
            if hasattr(self, field):
                self.set_property(field, value)

    def mount_for_create(self):
        return  # default is there's nothing extra to do

    def mount_for_create_many(self):
        return  # default is there's nothing extra to do

    def mount_for_update(self):
        view_kwargs = self.request.resolver_match.kwargs
        self.table_entry = self.table.objects.get(id=view_kwargs["table_entry_id"])
        # set initial data using the database and applying its values to
        # the form fields.
        config = self.to_db_dict(include_empties=True)
        for field in config:
            current_val = getattr(self.table_entry, field)
            self.set_property(field, current_val)

    def mount_for_update_many(self):
        # default is we want everything to be set to None, which includes
        # overriding default values
        for field in self.update_many_inputs:
            # opt for setattr instead of self.set_property since this is unsetting
            setattr(self, field, None)

    def mount_for_search(self):
        return  # default is there's nothing extra to do

    def mount_extra(self):
        return  # default is there's nothing extra to do

    # -------------------------------------------------------------------------

    def unmount(self):
        if self.form_mode == "create":
            self.unmount_for_create()
        elif self.form_mode == "create-many":
            self.unmount_for_create_many()
        elif self.form_mode == "update":
            self.unmount_for_update()
        elif self.form_mode == "update-many":
            self.unmount_for_update_many()
        elif self.form_mode == "search":
            self.unmount_for_search()
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

        all_updates = {
            field: value
            for field, value in config.items()
            if field not in self.ignore_on_update and field in self.update_many_inputs
        }

        # Special cases! Comments should be appended so nothing is lost, whereas
        # flat updates replace the col value entirely
        flat_updates = {}
        append_updates = {}
        for field, value in all_updates.items():
            if field == "comments" or field.endswith("_comments"):
                # TODO: allow other cols to be append type
                append_updates[field] = value
            else:
                flat_updates[field] = value

        self.final_updates = {
            "flat_updates": flat_updates,
            "append_updates": append_updates,
        }

    def unmount_for_search(self):
        return  # default is there's nothing extra to do

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
        # attempt casting to correct type
        new_value = parse_value(new_value)
        # buggy
        # from django_unicorn.typer import cast_attribute_value
        # new_value = cast_attribute_value(self, property_name, new_value)

        # check if there is a special defined method for this property
        method_name = f"set_{property_name}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(new_value, *args, **kwargs)
        else:
            setattr(self, property_name, new_value)

    # -------------------------------------------------------------------------

    def to_search_dict(self, **kwargs) -> dict:
        return self._get_default_search_dict(**kwargs)

    def _get_default_search_dict(self, include_empties: bool = False):
        # !!! consider merging functionality with _get_default_db_dict
        config = {}
        for form_attr in self.search_inputs:
            current_val = getattr(self, form_attr)
            current_val = parse_value(current_val)
            if not include_empties and current_val is None:
                continue
            config[form_attr] = current_val

        # comments should be a contains search
        if "comments" in config.keys():
            config["comments__contains"] = config.pop("comments")
        # reformat __in to python list
        if "id__in" in config.keys():
            # BUG: check to see it was input correctly?
            config["id__in"] = [int(i) for i in config["id__in"].split(";")]
        if "order_by" in config.keys() and self.reverse_order_by:
            config["order_by"] = "-" + config["order_by"]

        # TODO: should prob be in mol mixin
        # moleculequery's key depends on its type
        if "molecule" in config.keys():
            config[self.molecule_query_type] = self.get_molecule_obj().to_smiles()
            config.pop("molecule")

        return config

    # -------------------------------------------------------------------------

    # Model creation and update utils

    def to_db_dict(self, **kwargs) -> dict:
        return self._get_default_db_dict(**kwargs)

    def _get_default_db_dict(
        self,
        load_toolkits: bool = True,
        include_empties: bool = False,
    ) -> dict:
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
            current_val = parse_value(current_val)

            if not include_empties and current_val is None:
                continue

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

        if self.form_mode == "search":
            return self.get_search_redirect()  # has its own redirect
        else:
            self.presave_to_db()
            self.save_to_db()
            self.postsave_to_db()
            return self.get_submission_redirect()

    def presave_to_db(self):
        return  # default is there's nothing extra to do

    def save_to_db(self):
        if self.form_mode in ["create", "update"]:
            self.table_entry.save()
        elif self.form_mode == "update-many":

            flat_updates = self.final_updates["flat_updates"]
            append_updates = self.final_updates["append_updates"]

            # TODO: put this all within a single db transaction...?

            entries = self.table.objects.filter(id__in=self.entry_ids_to_update)

            if flat_updates:
                entries.update(**flat_updates)

            if append_updates:
                for entry in entries.all():
                    for field, append_value in append_updates.items():
                        current_value = getattr(entry, field)
                        new_value = current_value + "\n\n" + append_value
                        setattr(entry, field, new_value)
                        entry.save()
                        # OPTIMIZE: consider doing a bulk update at the end

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
        elif self.redirect_mode == "refresh":
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

    def get_search_redirect(self):  # *args, **kwargs

        # moleclue_query: str
        # self.set_molecule(moleclue_query, render=False)

        # grab all metadata filters and convert to url GET params
        filters = self.to_search_dict()

        # convert all values to json serialized strings
        filters_serialized = {k: json.dumps(v) for k, v in filters.items()}

        # encode any special characters for the url
        url_get_clause = urllib.parse.urlencode(filters_serialized)

        final_url = self.parent_url + "?" + url_get_clause
        return redirect(final_url)

    # -------------------------------------------------------------------------

    is_editting = False
    entries_for_create_many = []

    def apply_to_children(self):

        breakpoint()
        config = self.to_db_dict(
            include_empties=False,
            load_toolkits=False,
        )

        for attribute in self.attributes_to_apply:
            value = getattr(self, attribute)
            for child in self.children:
                print(str(child))
                if hasattr(child, attribute):
                    setattr(child, attribute, value)
                    print(f"{attribute}: {value}")
        # self.parent.force_render = True

    # -------------------------------------------------------------------------


def parse_value(value: str):
    # attempt casting to correct type bc AJAX/JSON always gives a string
    if isinstance(value, str):
        if value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit():
            value = float(value)
        elif value in ["None", "NONE", ""]:
            value = None
    return value
