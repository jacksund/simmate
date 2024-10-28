# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render
from django.views import View

from simmate.database.base_data_types import DatabaseTable
from simmate.website.utilities import get_pagination_urls


class DynamicApiView(View):
    """
    Abstract base class that enables dynamic API format (html vs. json) as well
    as (optionally) dynamic table selection via `get_table`. Setting a single
    table is also allowed via the `_table` attribute.

    This class is largely inspired by the GenericViewSet class in django
    rest_framework, where it was re-written for clarity, extra features, and
    better integration with Simmate database tables.
    """

    mode: str = None
    # options: 'list', 'entry', 'about', 'search', 'entry-new', and 'entry-update'

    @classmethod
    @property
    def about_view(cls):
        return cls.as_view(mode="about")

    @classmethod
    @property
    def list_view(cls):
        return cls.as_view(mode="list")

    @classmethod
    @property
    def search_view(cls):
        return cls.as_view(mode="search")

    @classmethod
    @property
    def entry_view(cls):
        return cls.as_view(mode="entry")

    @classmethod
    @property
    def entry_new_view(cls):
        return cls.as_view(mode="entry-new")

    @classmethod
    @property
    def entry_update_view(cls):
        return cls.as_view(mode="entry-update")

    def get(self, request, *args, **kwargs):
        """
        This is the main entrypoint for all GET requests.
        """

        # TODO: I could make this extra dynamic if there's ever a reason for it.
        #   getattr(f"get_{mode}_{format}_view")
        # For now, I just hardcode the options for mode and format.

        if not self.mode:
            raise Exception(
                "Make sure you initialize your view with `.as_view(mode=...)`."
                " Mode options are 'list', 'about', and 'entry'."
            )
        elif self.mode == "list":
            html_view = self.get_list_html_view
            json_view = self.get_list_json_view
        elif self.mode == "entry":
            html_view = self.get_entry_html_view
            json_view = self.get_entry_json_view
        elif self.mode == "search":
            html_view = self.get_search_html_view
            json_view = self.get_search_json_view
        elif self.mode == "entry-new":
            html_view = self.get_entry_new_html_view
            json_view = self.get_entry_new_json_view
        elif self.mode == "entry-update":
            html_view = self.get_entry_update_html_view
            json_view = self.get_entry_update_json_view
        elif self.mode == "about":
            html_view = self.get_about_html_view
            json_view = self.get_about_json_view
        else:
            raise Exception(f"Unknown 'mode' given: {self.mode}")

        # move to proper view function based on requested format
        view_format = request.GET.get("format", "html")  # default is html
        if view_format == "html":
            return html_view(request, *args, **kwargs)
        elif view_format == "json":
            # BUG: new/update/search should be POST, not GET
            return json_view(request, *args, **kwargs)
        else:
            raise Exception(f"Unknown 'format' GET arg given: {view_format}")

    # -------------------------------------------------------------------------

    _table: DatabaseTable = None
    """
    The table to use in building this view. Note, if the table is dynamically
    determined (via a custom `get_table` method), this should be left as `None`.
    
    Always use the `get_table` to grab the table, rather than this attribute.
    """

    _table_entry_kwarg: str = "table_entry_id"

    @classmethod
    def get_table(cls, request, *args, **kwargs) -> DatabaseTable:
        """
        grabs the relevant database table using the request.

        Some apps dynamically determine the table, so 'get_table' method is
        overwritten to do this.
        """
        if cls._table:
            return cls._table
        else:
            raise Exception(
                f"No `_table` attribute set for {cls.__name__}. Either set "
                "the table, or overwrite the `get_table` method."
            )

    @classmethod
    def get_table_entry(cls, request, *args, **kwargs) -> DatabaseTable:
        """
        grabs the relevant table entry using the request.

        By default, this uses the `_table_entry_kwarg` attribute in the URL
        config as the `pk`
        """
        table = cls.get_table(request, *args, **kwargs)
        return get_object_or_404(table, pk=kwargs[cls._table_entry_kwarg])

    # -------------------------------------------------------------------------

    # The "about" views, which give documentation for a given table

    def get_about_json_view(self, request, *args, **kwargs):
        raise NotImplementedError("JSON responses for tables is still under dev.")

    def get_about_html_view(self, request, *args, **kwargs):
        table = self.get_table(request, *args, **kwargs)
        context = {
            "table": table,
            "table_docs": table.get_table_docs(),
            # TODO: **table.html_extra_about_context,
        }
        template = table.html_about_template
        return render(request, template, context)

    # -------------------------------------------------------------------------

    # The "list" views for a single database table.
    # Includes filtering via GET params.

    def get_list_json_view(self, request, *args, **kwargs):
        table = self.get_table(request, *args, **kwargs)
        page = table.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        response = page.object_list.to_json_response(
            next_url=pagination_urls["next"],
            previous_url=pagination_urls["previous"],
        )
        return response

    def get_list_html_view(self, request, *args, **kwargs):
        table = self.get_table(request, *args, **kwargs)
        page = table.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        context = {
            "table": table,
            "page": page,
            "pagination_urls": pagination_urls,
            # "paginator": page.paginator,
            # "entries": page.object_list,  # page.paginator.object_list gives ALL results
            # TODO:
            **table.html_breadcrumb_context,
            **table.html_extra_context,
            # make left sidebar compact (only icons) when there's a quick-search
            # view, so that we can put the search form on the right side
            # "compact_sidebar": True if table.html_search_view else False,
        }
        template = table.html_table_template
        return render(request, template, context)

    # -------------------------------------------------------------------------

    # The "entry" view for a single database table. Uses IDs to get the entry.

    def get_entry_json_view(self, request, *args, **kwargs):
        table_entry = self.get_table_entry(request, *args, **kwargs)
        return table_entry.to_json_response()

    def get_entry_html_view(self, request, *args, **kwargs):
        table_entry = self.get_table_entry(request, *args, **kwargs)
        context = {
            "table_entry": table_entry,
            # TODO:
            # **table.html_entry_breadcrumb_context,
            # **table.html_entry_extra_context,
        }
        template = table_entry.html_entry_template
        return render(request, template, context)

    # -------------------------------------------------------------------------
    # Below are HTML Form views -- typically these are POST, but we use
    # django-unicorn which contains any POSTs within a component.
    # TODO: in the future, I may want to allow JSON post requests so that
    # rows can be added/updated via API calls. I don't do this yet because the
    # ORM is preferred + using admin permissions.
    # -------------------------------------------------------------------------

    # The "search" views, which build a search form for the table

    def get_search_json_view(self, request, *args, **kwargs):
        raise NotImplementedError("Search views still under dev.")

    def get_search_html_view(self, request, *args, **kwargs):
        raise NotImplementedError("Search views still under dev.")

    # -------------------------------------------------------------------------

    # The "entry-new" views, which are for creating one or more new rows

    def get_entry_new_json_view(self, request, *args, **kwargs):
        raise NotImplementedError("Entry-New views still under dev.")

    def get_entry_new_html_view(self, request, *args, **kwargs):
        raise NotImplementedError("Entry-New views still under dev.")

    # -------------------------------------------------------------------------

    # The "entry-update" views, which are for editting one or more existing rows

    def get_entry_update_json_view(self, request, *args, **kwargs):
        raise NotImplementedError("Entry-Update views still under dev.")

    def get_entry_update_html_view(self, request, *args, **kwargs):
        raise NotImplementedError("Entry-Update views still under dev.")

    # -------------------------------------------------------------------------
