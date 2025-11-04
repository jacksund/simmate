# -*- coding: utf-8 -*-

from django.shortcuts import redirect

from simmate.database.base_data_types import DatabaseTable
from simmate.toolkit import Molecule, Structure
from simmate.website.utilities import parse_request_get

from .base import HtmxComponent
from .dynamic_table_form_mixins import (
    CreateManyMixin,
    CreateMixin,
    SearchMixin,
    UpdateManyMixin,
    UpdateMixin,
)


class DynamicTableForm(
    HtmxComponent,
    CreateManyMixin,
    CreateMixin,
    SearchMixin,
    UpdateManyMixin,
    UpdateMixin,
):
    """
    The abstract base class for dynamic front-end views.
    """

    # -------------------------------------------------------------------------

    template_names: dict = {}
    """
    The location of the templates to use for this component. The keys should
    be form modes (with an option to have a 'default' key) and the values
    should be the template name.
    """

    @property
    def template_name(self):
        return (
            self.template_names.get(self.form_mode)
            if self.form_mode in self.template_names
            else self.template_names["default"]
        )

    # -------------------------------------------------------------------------

    form_mode: str = None
    """
    The mode the form is currently in. Options are "create", "update", 
    "update_many", "create_many", "create_many_entry, and "search".
    
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
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------

    def submit_form(self):

        # check form is valid
        if not self.check_form():
            return

        # then call series of final hooks
        self.unmount()
        self.presave_to_db()
        self.save_to_db()
        self.postsave_to_db()

        return self.get_submission_redirect()

    # -------------------------------------------------------------------------

    def mount(self):

        self.mount_form_mode()

        # Call the corresponding mount() method based on our mode
        if self.form_mode == "create":
            self.mount_for_create()
        elif self.form_mode == "create_many":
            self.mount_for_create_many()
        elif self.form_mode == "create_many_entry":
            self.mount_for_create()
            self.is_editting = False
        elif self.form_mode == "update":
            self.mount_for_update()
        elif self.form_mode == "update_many":
            self.mount_for_update_many()
        elif self.form_mode == "search":
            self.mount_for_search()
        else:
            raise Exception(f"Unknown form_mode is set: {self.form_mode}")

        self.mount_url_info()
        self.mount_extra()

    def mount_form_mode(self):

        view_name = self.request.resolver_match.url_name

        # Dynamically determine form_mode using the view name if it is not
        # specified in the html template directly
        if not self.form_mode:
            if view_name == "table-entry-new":
                self.form_mode = "create"
            elif view_name == "table-entry-update":
                self.form_mode = "update"
            elif view_name == "table-entry-update-many":
                self.form_mode = "update_many"
            elif view_name == "table-entry-new-many":
                self.form_mode = "create_many"
            elif view_name == "table-entry-search":
                self.form_mode = "search"
            else:
                raise Exception(f"Unknown view type for dynamic form: {view_name}")

        # check that mode is actually allowed
        if self.form_mode not in self.table.html_enabled_forms:
            raise Exception(
                f"The form mode '{self.form_mode}' is disabled for this table."
            )

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
        self.form_data.update(get_kwargs)

    def mount_extra(self):
        return  # default is there's nothing extra to do

    # -------------------------------------------------------------------------

    form_errors = []

    def check_form(self) -> bool:
        # reset errors for this new check
        self.form_errors = []

        if self.skip_db_save:
            return True

        if self.form_mode == "create":
            self.check_form_for_create()
        elif self.form_mode == "create_many":
            self.check_form_for_create_many()
        elif self.form_mode == "update":
            self.check_form_for_update()
        elif self.form_mode == "update_many":
            self.check_form_for_update_many()
        elif self.form_mode == "search":
            self.check_form_for_search()
        else:
            raise Exception(f"Unknown form_mode is set: {self.form_mode}")

        self.check_form_hook()

        return True if not self.form_errors else False

    def check_form_hook(self) -> bool:
        return True  # default is there's nothing extra to check

    def check_required_inputs(self):
        # Check that all basic inputs are filled out
        for input_name in self.required_inputs:
            input_value = self.form_data.get(input_name, None)
            if input_value in [None, "", []]:
                message = f"'{input_name}' is a required input."
                self.form_errors.append(message)

    # -------------------------------------------------------------------------

    def unmount(self):
        if self.form_mode == "create":
            self.unmount_for_create()
        elif self.form_mode == "create_many":
            self.unmount_for_create_many()
        elif self.form_mode == "update":
            self.unmount_for_update()
        elif self.form_mode == "update_many":
            self.unmount_for_update_many()
        elif self.form_mode == "search":
            self.unmount_for_search()
        else:
            raise Exception(f"Unknown form_mode is set: {self.form_mode}")

        self.unmount_extra()

    def unmount_extra(self):
        return  # default is there's nothing extra to do

    # -------------------------------------------------------------------------

    skip_db_save: bool = False

    def presave_to_db(self):
        return  # default is there's nothing extra to do

    def save_to_db(self):

        if self.skip_db_save:
            return

        if self.is_subform:

            # ensure the parent obj has been saved and has an id
            if not (
                self.parent and self.parent.table_entry and self.parent.table_entry.id
            ):
                raise Exception("parent object must be saved first")
            setattr(self.table_entry, self.subform_pointer, self.parent.table_entry.id)

        if self.form_mode == "create":
            self.save_to_db_for_create()
        elif self.form_mode == "create_many":
            self.save_to_db_for_create_many()
        elif self.form_mode == "update":
            self.save_to_db_for_update()
        elif self.form_mode == "update_many":
            self.save_to_db_for_update_many()
        elif self.form_mode == "search":
            self.save_to_db_for_search()
        else:
            raise Exception(f"Unknown form_mode is set: {self.form_mode}")

    def postsave_to_db(self):
        return  # default is there's nothing extra to do

    # -------------------------------------------------------------------------

    # Model creation and update utils

    def to_db_dict(
        self,
        load_toolkits: bool = True,
        include_empties: bool = False,
    ) -> dict:

        # By default, we say the form maps to columns of the model with same name.
        # We also check for direct relations, which would end in "_id"
        # (e.g. 'created_by_id' for users where col is technically 'created_by')
        # We also ignore *_to_many relations because these are saved using
        # child components
        table_cols = [
            column.name
            for column in self.table.columns
            if not column.one_to_many and not column.many_to_many
        ]

        matching_fields = [
            key
            for key in self.form_data.keys()
            if key in table_cols or (key.endswith("_id") and key[:-3] in table_cols)
        ]

        config = {}
        for form_key in matching_fields:
            current_val = self.form_data[form_key]

            if not include_empties and current_val is None:
                continue

            config[form_key] = current_val

            # special data types and common field names. Note, variations
            # of this should be handled by overriding the `to_db_dict`
            if (
                load_toolkits
                and current_val is not None
                and self.form_mode != "create_many"
            ):
                if form_key == "molecule":
                    config["molecule_original"] = current_val
                    config["molecule"] = Molecule.from_dynamic(current_val)
                elif form_key == "structure":
                    config["structure_original"] = current_val
                    config["structure"] = Structure.from_dynamic(current_val)

        return config

    # -------------------------------------------------------------------------

    # To help with page redirects after submission

    redirect_mode: str = "table_entry"
    """
    Controls which page the user is redirected to after form submission. 
    Options are "table_entry", "table", "refresh", and "no_redirect"
    """

    parent_url: str = None
    """
    The original URL where this form is embeded. This attr is primarily for
    the data "table" view where there are many forms, and after the form is
    submitted, we'd want to refresh the parent url (including any GET kwargs)
    """

    def get_submission_redirect(self):
        if self.form_mode == "search":
            # has its own unique redirect that takes priority
            return self.get_search_redirect()

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
        elif self.redirect_mode == "no_redirect":
            return None
        else:
            raise Exception(
                f"Unknown redirect_mode for dynamic form: {self.redirect_mode}"
            )

    # -------------------------------------------------------------------------
