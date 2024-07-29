# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.views import View

from simmate.database.base_data_types import DatabaseTable
from simmate.website.utilities import get_pagination_urls

# class SimmateApiViewDEV(View):
#     # get --> decides if list or entry, then calls one of...
#     #   get_about_reponse (docs)
#     #   get_list_response (filtered table using GET args)
#     #   get_entry_response (single row using ID)


class DatabaseTableView(View):

    # -------------------------------------------------------------------------

    # This is the main entrypoint for all GET requests.

    def get(self, request, *args, **kwargs):
        # move to proper view function based on requested format
        view_format = request.GET.get("format", "html")
        if view_format == "html":
            return self.get_html_view(request, *args, **kwargs)
        elif view_format == "json":
            return self.get_json_view(request, *args, **kwargs)
        else:
            raise Exception(f"Unknown 'format' GET arg given: {view_format}")

    # -------------------------------------------------------------------------

    # Defines how the table is determined. Some apps dynamically determine
    # the table, so 'get_table' method is overwritten to do this.

    _table: DatabaseTable = None
    """
    The table to use in building this view. Note, if the table is dynamically
    determined (via a custom `get_table` method), this should be left as `None`.
    
    Always use the `get_table` to grab the table, rather than this attribute.
    """

    @classmethod
    def get_table(cls, request, *args, **kwargs) -> DatabaseTable:
        """
        grabs the relevant database table using the URL request
        """
        if cls._table:
            return cls._table
        else:
            raise Exception(
                f"No `_table` attribute set for {cls.__name__}. Either set "
                "the table, or overwrite the `get_table` method."
            )

    # -------------------------------------------------------------------------

    def get_json_view(self, request, *args, **kwargs):
        table = self.get_table(request, *args, **kwargs)
        page = table.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        response = page.object_list.to_json_response(
            next_url=pagination_urls["next"],
            previous_url=pagination_urls["previous"],
        )
        return response

    def get_html_view(self, request, *args, **kwargs):
        table = self.get_table(request, *args, **kwargs)
        page = table.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        context = {
            "page_title": "The Discovery Lab App",
            "breadcrumbs": [("data_explorer:home", "Data")],
            "breadcrumb_active": table.table_name,
            "table": table,
            "page": page,
            "pagination_urls": pagination_urls,
            # "paginator": page.paginator,
            # "entries": page.object_list,  # page.paginator.object_list gives ALL results
            # extra optional unicorn views (link to db model?)
            "quick_search_view": "cortevatarget-search",
            "updater_view": "cortevatarget-update-many",
            "add_new_view": 123,  # TODO: switch to view
            # TODO:
            # **self.table.extra_html_context,
        }
        # template = "data_explorer/table.html"
        template = "discovery_lab/cortevatarget_full.html"
        return render(request, template, context)

    # -------------------------------------------------------------------------
