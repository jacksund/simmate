# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from simmate.configuration import settings
from simmate.database.base_data_types import DatabaseTable
from simmate.database.utilities import get_table
from simmate.website.utilities import get_pagination_urls

# -----------------------------------------------------------------------------

# We build this dict up front to reduce overhead on all API calls.
_SAFE_TABLES = {
    get_table(table_name).table_name: get_table(table_name)
    for section_name, table_names in settings.website.data.items()
    for table_name in table_names
}


def get_table_safe(table_name: str) -> DatabaseTable:
    """
    Utilitiy to grab the relevant database table using the table name or import path.

    Note, this only grabs tables from what is allowed via the `website.data`
    setting. We don't use the `get_table` utility, which is permissionless -- as
    that could grab sensitive tables, such as those with API keys or passwords
    hashes.
    """
    provider_table = _SAFE_TABLES[table_name]
    return provider_table


def get_table_entry_safe(table_name: str, table_entry_id: str | int) -> DatabaseTable:
    """
    Grabs the relevant table entry using the request using the pk/id
    """
    table = get_table_safe(table_name)
    return get_object_or_404(table, pk=table_entry_id)


# -----------------------------------------------------------------------------


def home(request):

    # Uses the settings to build out Data sections + associated list of tables
    # within each section. There is also a HIDDEN section that is handled
    # the same here. The html template handles that case separately.
    #
    # Note: We don't need `get_table_safe` here because we are building directly
    # from the settings
    data_config = {}
    for section_name, table_list in settings.website.data.items():
        data_config[section_name] = [get_table(table_name) for table_name in table_list]

    context = {
        "data_config": data_config,
        "breadcrumbs": ["Data"],
    }
    template = "data_explorer/home.html"
    return render(request, template, context)


def table_about(request, table_name):
    table = get_table_safe(table_name)
    context = {
        "table": table,
        "table_docs": table.get_table_docs(),
        # TODO: **table.html_extra_about_context,
        "page_title": table_name,
        "breadcrumbs": ["Data", table_name, "About"],
    }
    template = table.html_about_template
    return render(request, template, context)


def table_entries(request, table_name):

    table = get_table_safe(table_name)
    view_format = request.GET.get("format", "html")  # default is html

    if view_format == "html":
        page = table.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        context = {
            "table": table,
            "page": page,
            "pagination_urls": pagination_urls,
            "total": page.paginator.count,  # often limited to 10k
            # "paginator": page.paginator,
            # "entries": page.object_list,  # page.paginator.object_list gives ALL results
            "page_title": table_name,
            "page_title_icon": "mdi-database",
            "breadcrumbs": ["Data", table_name],
            "title_json_link": True,
            **table.html_extra_table_context,
            # make left sidebar compact (only icons) when there's a quick-search
            # view, so that we can put the search form on the right side
            # "compact_sidebar": True if table.html_search_view else False,
        }
        template = table.html_table_template
        return render(request, template, context)

    elif view_format == "json":
        page = table.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        return page.object_list.to_json_response(
            next_url=pagination_urls["next"],
            previous_url=pagination_urls["previous"],
        )

    elif view_format == "csv":
        # CSV is a unique case where we do a bulk download (up to 10k rows or
        # whatever limit is set by filter_from_config).
        objects = table.filter_from_request(request, paginate=False)

        # https://stackoverflow.com/questions/54729411/
        df = objects.to_dataframe()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f"attachment; filename={table_name}_queryset.csv"
        )
        df.to_csv(path_or_buf=response, index=False)
        return response

    else:
        raise Exception(f"Unknown 'format' GET arg given: {view_format}")


def table_entry(request, table_name, table_entry_id):

    table_entry = get_table_entry_safe(table_name, table_entry_id)

    # move to proper view function based on requested format
    view_format = request.GET.get("format", "html")  # default is html

    if view_format == "html":
        context = {
            "table_entry": table_entry,
            "page_title": "Table Entry",
            "breadcrumbs": ["Data", table_name, table_entry_id],
            "title_json_link": True,
            **table_entry.html_extra_entry_context,
        }
        template = table_entry.html_entry_template
        return render(request, template, context)

    elif view_format == "json":
        return table_entry.to_json_response()

    else:
        raise Exception(f"Unknown 'format' GET arg given: {view_format}")


def table_search(request, table_name):
    raise NotImplementedError("Search view still under dev.")


# -------------------------------------------------------------------------
# Below are HTML Form views -- typically these are POST, but we use
# django-unicorn which contains any POSTs within a component (AJAX requests).
#
# TODO: in the future, I may want to allow JSON post requests so that
# rows can be added/updated via API calls. I don't do this yet because the
# ORM is preferred + using admin permissions.
# -------------------------------------------------------------------------


def table_entry_new(request, table_name):

    table = get_table_safe(table_name)
    if not table.html_form_view:
        raise NotImplementedError("This model does not have an 'entry-new' view yet!")

    context = {
        "unicorn_component_name": table.html_form_view,
        "page_title": table_name,
        "page_title_icon": "mdi-database",
        "breadcrumbs": ["Data", table_name, "Form"],
    }
    template = table.html_entry_form_template
    return render(request, template, context)


def table_entry_new_many(request, table_name):
    # We can just use the entry-new view because our underlying unicorn
    # view will dynamically determine this using the URL path
    return table_entry_new(request, table_name)


def table_entry_update(request, table_name, table_entry_id):
    # We can just use the entry-new view because our underlying unicorn
    # view will dynamically determine this using the URL path
    return table_entry_new(request, table_name)
