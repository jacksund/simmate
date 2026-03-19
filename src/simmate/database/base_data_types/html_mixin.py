# -*- coding: utf-8 -*-

import pandas


class HTMLMixin:
    """
    Mixin that defines how the table and web views work within the
    website.data_explorer app.

    NOTE: This class is deprecated and will be refactored to be a part of the
    htmx component base class in the future.
    """

    # -------------------------------------------------------------------------
    # Methods that link to the website UI
    # -------------------------------------------------------------------------

    # experimental overrides for templates used by the Data Explorer app

    html_display_name: str = None
    html_description_short: str = None
    html_tabtitle_label_col: str = "id"

    html_about_template: str = "data_explorer/table_about.html"
    html_table_template: str = "data_explorer/table.html"
    html_entry_template: str = "data_explorer/table_entry.html"
    html_entries_template: str = "data_explorer/table_entries.html"

    # This take the views below and just put them within the main body
    html_search_template: str = "htmx/full_page_component.html"
    html_entry_form_template: str = "htmx/full_page_component.html"

    # HTMX views (side panels in the table view of the Data Explorer app)
    html_form_component: str = None
    html_enabled_forms: list[str] = []
    # options: "search", "create", "update", "create_many", "create_many_entry", "update_many"

    @property
    def html_tabtitle_label(self) -> str:
        """
        Provides a label to put in the tab title. By default, this uses the id
        """
        return str(getattr(self, self.html_tabtitle_label_col))

    @classmethod
    @property
    def html_extra_table_context(cls) -> dict:
        return {}

    @property
    def html_extra_entry_context(self) -> dict:
        return {}

    # -------------------------------------------------------------------------
    # Methods for reports and plotting.
    # -------------------------------------------------------------------------

    # Note, many methods associated with this section would normally be
    # attached to custom QuerySet/SearchResults subclasses, but that leads
    # to extra boiler plate.

    enable_html_report: bool = False
    report_df_columns: list[str] = None

    @classmethod
    def get_report(cls, data_source=None) -> dict:
        """
        Gives a dictionary of report information, such as statistical values
        or plotly figures.

        If data_source is left as None, the entire table is used
        """
        # We avoid direct imports of SearchResults and Page to prevent
        # circular imports with the base_data_types.base module.

        # convert to a SearchResults/queryset obj
        if data_source == None:
            data_source = cls.objects  # use full table by default
        elif hasattr(data_source, "paginator"):  # checks if it's a Page object
            data_source = data_source.paginator.object_list

        df = data_source.to_dataframe(cls.report_df_columns)
        return cls.get_report_from_df(df)

    @classmethod
    def get_report_from_df(cls, df: pandas.DataFrame) -> dict:
        raise NotImplementedError("A `get_report_from_df` method must be provided")
