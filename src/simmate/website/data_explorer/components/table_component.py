# -*- coding: utf-8 -*-

from django.shortcuts import redirect

from simmate.database.core import DatabaseTable
from simmate.website.htmx.components import HtmxComponent
from simmate.website.utils import parse_request_get

from .dynamic_table_form_mixins import (
    CreateManyMixin,
    CreateMixin,
    DashboardMixin,
    EntriesMixin,
    EntryMixin,
    ReportMixin,
    SearchMixin,
    UpdateManyMixin,
    UpdateMixin,
)


class TableComponent(
    HtmxComponent,
    CreateManyMixin,
    CreateMixin,
    DashboardMixin,
    EntriesMixin,
    EntryMixin,
    ReportMixin,
    SearchMixin,
    UpdateManyMixin,
    UpdateMixin,
):
    """
    The abstract base class for dynamic front-end views that interact with
    a database table.
    """

    enabled_component_types: list[str] = [
        "dashboard",
        "entries",
        "entry",
    ]
    """
    Component types that are enabled for this table explorer view.
    """

    component_type: str = None
    """
    The type of component this is. Options are:
        - dashboard
        - entries
        - entry
        - report
        - search
        - create
        - update
        - update_many
        - create_many
        - create_many_entry
    
    In some cases this does not need to be set because it can be inferred from
    the parent_url (e.g. `example/1234/update` url = update mode). See
    `mount_component_type` for how this is dynamically set.
    """

    table: DatabaseTable = None  # class object
    """
    The database table that this component is intended to work with.
    """

    table_entry: DatabaseTable = None  # initialized object
    """
    If component_type is "entry", "create", or "update", this is the single 
    table entry that is being interacted with. This is set dynamically.
    """

    template_names: dict = {}
    """
    The location of the templates to use for this component. The keys should
    be component types (with an option to have a 'default' key) and the values
    should be the template name.
    """

    @property
    def template_name(self):
        if self.component_type in self.template_names:
            return self.template_names[self.component_type]
        elif "default" in self.template_names:
            return self.template_names["default"]
        elif self.component_type == "dashboard":
            return "data_explorer/dashboard.html"
        # TODO: consider adding default templates for other types
        else:
            raise Exception(
                f"No template defined for component_type: {self.component_type}"
            )

    # -------------------------------------------------------------------------

    @classmethod
    @property
    def display_name(cls):
        return cls.table.table_name

    @classmethod
    @property
    def description_short(cls):
        return ""

    @property
    def num_rows_cache(self) -> int | None:
        """
        The number of rows in this table, typically cached by a background process.
        """
        from simmate.website.data_explorer.models import TableCount

        try:
            return TableCount.objects.get(table_name=self.table.table_name).row_count
        except:
            return None

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

        self.mount_component_type()

        # Call the corresponding mount() method based on our type
        if self.component_type == "dashboard":
            self.mount_for_dashboard()
        elif self.component_type == "entries":
            self.mount_for_entries()
        elif self.component_type == "entry":
            self.mount_for_entry()
        elif self.component_type == "report":
            self.mount_for_report()
        elif self.component_type == "search":
            self.mount_for_search()
        elif self.component_type == "create":
            self.mount_for_create()
        elif self.component_type == "create_many":
            self.mount_for_create_many()
        elif self.component_type == "create_many_entry":
            self.mount_for_create()
        elif self.component_type == "update":
            self.mount_for_update()
        elif self.component_type == "update_many":
            self.mount_for_update_many()
        else:
            raise Exception(f"Unknown component_type is set: {self.component_type}")

        self.mount_url_info()
        self.mount_extra()

    def mount_component_type(self):

        # Dynamically determine component_type using the view name if it is not
        # specified in the html template directly
        if self.request and not self.component_type:
            view_name = self.request.resolver_match.url_name
            if view_name == "table":
                self.component_type = "entries"
            elif view_name == "table-about":
                self.component_type = "dashboard"
            elif view_name == "table-entry":
                self.component_type = "entry"
            elif view_name == "table-entry-new":
                self.component_type = "create"
            elif view_name == "table-entry-update":
                self.component_type = "update"
            elif view_name == "table-entry-update-many":
                self.component_type = "update_many"
            elif view_name == "table-entry-new-many":
                self.component_type = "create_many"
            elif view_name == "table-entry-search" or view_name == "table-search":
                self.component_type = "search"
            else:
                raise Exception(f"Unknown view type for component: {view_name}")

        # check that type is actually allowed
        if self.component_type not in self.enabled_component_types:
            raise Exception(
                f"The component type '{self.component_type}' is disabled for this table."
            )

    def mount_url_info(self):
        # grab parent url for resubmission. We include GET params unless the
        # mode is search, in which case we only want the base path.
        self.parent_url = (
            self.request.path
            if self.component_type == "search"
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

        if self.component_type in ["dashboard", "entries", "entry", "report"]:
            return True  # these types do not submit data

        if self.component_type == "create":
            self.check_form_for_create()
        elif self.component_type == "create_many":
            self.check_form_for_create_many()
        elif self.component_type == "create_many_entry":
            self.check_form_for_create()
        elif self.component_type == "update":
            self.check_form_for_update()
        elif self.component_type == "update_many":
            self.check_form_for_update_many()
        elif self.component_type == "search":
            self.check_form_for_search()
        else:
            raise Exception(f"Unknown component_type is set: {self.component_type}")

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
        if self.component_type in ["dashboard", "entries", "entry", "report"]:
            pass  # no specific unmount for these yet
        elif self.component_type == "create":
            self.unmount_for_create()
        elif self.component_type == "create_many":
            self.unmount_for_create_many()
        elif self.component_type == "create_many_entry":
            self.unmount_for_create()
        elif self.component_type == "update":
            self.unmount_for_update()
        elif self.component_type == "update_many":
            self.unmount_for_update_many()
        elif self.component_type == "search":
            self.unmount_for_search()
        else:
            raise Exception(f"Unknown component_type is set: {self.component_type}")

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

        if self.component_type in ["dashboard", "entries", "entry", "report"]:
            return  # these types do not save data

        if self.component_type == "create":
            self.save_to_db_for_create()
        elif self.component_type == "create_many":
            self.save_to_db_for_create_many()
        elif self.component_type == "create_many_entry":
            self.save_to_db_for_create()
        elif self.component_type == "update":
            self.save_to_db_for_update()
        elif self.component_type == "update_many":
            self.save_to_db_for_update_many()
        elif self.component_type == "search":
            self.save_to_db_for_search()
        else:
            raise Exception(f"Unknown component_type is set: {self.component_type}")

    def postsave_to_db(self):
        return  # default is there's nothing extra to do

    # -------------------------------------------------------------------------

    # To help with page redirects after submission

    redirect_mode: str = "table_entry"
    """
    Controls which page the user is redirected to after form submission. 
    Options are "table_entry", "table", "refresh", and "no_redirect"
    """

    parent_url: str = None
    """
    The original URL where this component is embeded. This attr is primarily for
    the data "table" view where there are many forms, and after the form is
    submitted, we'd want to refresh the parent url (including any GET kwargs)
    """

    def get_submission_redirect(self):
        if self.component_type == "search":
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
                f"Unknown redirect_mode for component: {self.redirect_mode}"
            )

    # -------------------------------------------------------------------------

    @classmethod
    def get_extra_table_context(cls, request) -> dict:
        return {}  # default to nothing extra

    @classmethod
    def get_extra_entry_context(cls, request, table_entry) -> dict:
        return {}  # default to nothing extra

    # -------------------------------------------------------------------------
