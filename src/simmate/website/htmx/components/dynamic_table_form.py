# -*- coding: utf-8 -*-

from django.shortcuts import redirect

from simmate.database.core import DatabaseTable
from simmate.website.utils import parse_request_get

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

    template_names: dict = {
        "default": "data_explorer/table_about.html",
        "table": "data_explorer/table.html",
        "entry": "data_explorer/table_entry.html",
        "entries": "data_explorer/table_entries.html",
        "create": "htmx/full_page_component.html",
        "update": "htmx/full_page_component.html",
        "create_many": "htmx/full_page_component.html",
        "search": "htmx/full_page_component.html",
    }
    """
    The location of the templates to use for this component. The keys should
    be form modes (with an option to have a 'default' key) and the values
    should be the template name.
    """

    @property
    def about_template(self):
        return (
            self.template_names["default"]
            if "default" in self.template_names
            else getattr(self.table, "html_about_template", "data_explorer/table_about.html")
        )

    @property
    def table_template(self):
        return (
            self.template_names["table"]
            if "table" in self.template_names
            else getattr(self.table, "html_table_template", "data_explorer/table.html")
        )

    @property
    def entry_template(self):
        return (
            self.template_names["entry"]
            if "entry" in self.template_names
            else getattr(self.table, "html_entry_template", "data_explorer/table_entry.html")
        )

    @property
    def entries_template(self):
        return (
            self.template_names["entries"]
            if "entries" in self.template_names
            else getattr(self.table, "html_entries_template", "data_explorer/table_entries.html")
        )

    @property
    def display_name(self):
        return (
            self.html_display_name
            if self.html_display_name
            else getattr(self.table, "html_display_name", self.table.table_name)
        )

    @property
    def description_short(self):
        return (
            self.html_description_short
            if self.html_description_short
            else getattr(self.table, "html_description_short", "")
        )

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

    # HTMX views (side panels in the table view of the Data Explorer app)
    html_form_component: str = None
    html_enabled_forms: list[str] = []
    # options: "search", "create", "update", "create_many", "create_many_entry", "update_many"

    @property
    def enabled_forms(self):
        return (
            self.html_enabled_forms
            if self.html_enabled_forms
            else getattr(self.table, "html_enabled_forms", [])
        )

    @property
    def form_component(self):
        return (
            self.html_form_component
            if self.html_form_component
            else getattr(self.table, "html_form_component", None)
        )

    # Methods for reports and plotting.
    enable_html_report: bool = False
    report_df_columns: list[str] = None

    def get_report(self, data_source=None) -> dict:
        if not self.enable_html_report and not getattr(
            self.table, "enable_html_report", False
        ):
            return {}

        # convert to a SearchResults/queryset obj
        if data_source == None:
            data_source = self.table.objects  # use full table by default
        elif hasattr(data_source, "paginator"):  # checks if it's a Page object
            data_source = data_source.paginator.object_list

        columns = (
            self.report_df_columns
            if self.report_df_columns
            else getattr(self.table, "report_df_columns", None)
        )
        df = data_source.to_dataframe(columns)

        # we prefer the method on the component, but fallback to the table
        if hasattr(self, "get_report_from_df"):
            return self.get_report_from_df(df)
        elif hasattr(self.table, "get_report_from_df"):
            return self.table.get_report_from_df(df)
        else:
            return {}

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
        if self.form_mode not in self.enabled_forms:
            raise Exception(
                f"The form mode '{self.form_mode}' is disabled for this table."
            )

    def get_table_docs(self) -> dict:
        """
        Grabs table metadata and column descriptions into a single dictionary
        """
        import textwrap

        return {
            "name": self.display_name,
            "table_info": {
                "sql_name": self.table._meta.db_table,
                "python_name": self.table.__name__,
                "python_path": self.table.__module__,
                "website_url": getattr(self.table, "url_table", None),
            },
            "table_description": textwrap.dedent(self.table.__doc__).strip(),
            "column_descriptions": self.table.get_column_docs(),
        }

    def show_table_docs(self, print_out: bool = True) -> str:
        """
        Prints all docs about this table. While a GUI is much better for exploring
        table docs, this method is more useful for outputting text that LLM
        chatbots can use.
        """
        # OPTIMIZE: still need to figure out what format works best with chatbots

        docs = self.get_table_docs()

        # we build the string before printing anything out
        final_str = ""

        final_str += f"# {docs['name']}\n\n"

        final_str += (
            "## About\n\n"
            f"\t- Python Class Name: {docs['table_info']['python_name']}\n"
            f"\t- Python Import Path: {docs['table_info']['python_path']}\n"
            f"\t- SQL Table Name: {docs['table_info']['sql_name']}\n"
            f"\t- Website UI Location: {docs['table_info']['website_url']}\n\n"
        )

        final_str += "## Table Description\n\n" f"{docs['table_description']}\n\n"

        final_str += "## Column Descriptions\n\n"
        for col_name, col_descr in docs["column_descriptions"].items():
            final_str += f"### `{col_name}`\n{col_descr}\n\n"

        if print_out:
            print(final_str)
        else:
            return final_str

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
        elif self.form_mode == "create_many_entry":
            self.check_form_for_create()
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
        elif self.form_mode == "create_many_entry":
            self.unmount_for_create()
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

        # if self.is_subform:
        #     # ensure the parent obj has been saved and has an id
        #     if not (
        #         self.parent and self.parent.table_entry and self.parent.table_entry.id
        #     ):
        #         raise Exception("parent object must be saved first")
        #     setattr(self.table_entry, self.subform_pointer, self.parent.table_entry.id)

        if self.form_mode == "create":
            self.save_to_db_for_create()
        elif self.form_mode == "create_many":
            self.save_to_db_for_create_many()
        elif self.form_mode == "create_many_entry":
            self.save_to_db_for_create()
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
