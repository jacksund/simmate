# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render

from simmate.config import settings
from simmate.database.core import DatabaseTable
from simmate.website.htmx.utils import get_component
from simmate.website.utils import get_pagination_urls

# -----------------------------------------------------------------------------


def get_data_explorer_components() -> dict:
    """
    Uses the settings to build out Data sections + associated list of components
    within each section.
    """
    data_config = {}
    for section_name, entry_list in settings.website.data.items():
        data_config[section_name] = []
        for name in entry_list:
            component = get_component(name)
            data_config[section_name].append(component)
    return data_config


# We build this dict up front to reduce overhead on all API calls.
_SAFE_COMPONENTS = {
    component.table.table_name: component
    for section_name, components in get_data_explorer_components().items()
    for component in components
}


def get_table_safe(table_name: str) -> DatabaseTable:
    """
    Utilitiy to grab the relevant database table using the table name or import path.

    Note, this only grabs tables from what is allowed via the `website.data`
    setting. We don't use the `get_table` utility, which is permissionless -- as
    that could grab sensitive tables, such as those with API keys or passwords
    hashes.
    """
    component = _SAFE_COMPONENTS[table_name]
    return component.table


def get_table_entry_safe(table_name: str, table_entry_id: str | int) -> DatabaseTable:
    """
    Grabs the relevant table entry using the request using the pk/id
    """
    table = get_table_safe(table_name)
    return get_object_or_404(table, pk=table_entry_id)


# -----------------------------------------------------------------------------


def home(request):

    from simmate.website.data_explorer.models import TableCount

    # Grab all counts at once to prevent N+1 queries
    counts_dict = dict(TableCount.objects.values_list("table_name", "row_count"))

    # Uses the settings to build out Data sections + associated list of tables
    # within each section. There is also a HIDDEN section that is handled
    # the same here. The html template handles that case separately.
    context = {
        "data_config": get_data_explorer_components(),
        "counts_dict": counts_dict,
        "breadcrumbs": ["Data"],
    }
    template = "data_explorer/home.html"
    return render(request, template, context)


def table_about(request, table_name):
    component = _SAFE_COMPONENTS[table_name]
    table = component.table
    context = {
        "table": table,
        "table_docs": table.get_table_docs(),
        **getattr(component, "extra_about_context", {}),
        "page_title": table_name,
        "breadcrumbs": ["Data", table_name, "About"],
    }
    template = component.template_names.get("about", "data_explorer/about.html")
    return render(request, template, context)


def table_entries(request, table_name):

    component_class = _SAFE_COMPONENTS[table_name]
    component = component_class(component_type="dashboard", request=request)

    # TODO: support datastores
    table = component.table

    # check whether this is a web ui, API, or download request
    view_format = request.GET.get("format", "html")

    if view_format == "html":
        page = table.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        context = {
            "component": component,
            "table": table,
            "page": page,
            "pagination_urls": pagination_urls,
            "total": page.paginator.count,  # often limited to 10k
            "report": component.get_report(page),
            # "paginator": page.paginator,
            # "entries": page.object_list,  # page.paginator.object_list gives ALL results
            "page_title": table_name,
            "page_title_icon": "mdi-database",
            "breadcrumbs": ["Data", component.display_name],
            "title_json_link": True,
            **component.get_extra_table_context(request),
        }
        template = component.template_name
        return render(request, template, context)

    elif view_format == "json":
        page = table.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        return page.object_list.to_json_response(
            next_url=pagination_urls["next"],
            previous_url=pagination_urls["previous"],
        )

    elif view_format == "csv":
        objects = table.filter_from_request(request, paginate=False)
        return objects.to_csv_response(mode="api")

    elif view_format == "curated-csv":
        objects = table.filter_from_request(request, paginate=False)
        return objects.to_csv_response(mode="curated")

    # TODO: add support for CIF, SDF, and other mol/crystal formats

    else:
        raise Exception(f"Unknown 'format' GET arg given: {view_format}")


def table_entry(request, table_name, table_entry_id):

    component_class = _SAFE_COMPONENTS[table_name]
    table_entry = get_table_entry_safe(table_name, table_entry_id)

    # move to proper view function based on requested format
    view_format = request.GET.get("format", "html")  # default is html

    if view_format == "html":
        context = {
            "table_entry": table_entry,
            "page_title": "Table Entry",
            "breadcrumbs": [
                "Data",
                component_class.display_name,
                table_entry_id,
            ],
            "title_json_link": True,
            **component_class.get_extra_entry_context(request, table_entry),
        }
        template = component_class.template_names.get(
            "entry", "data_explorer/entry.html"
        )
        return render(request, template, context)

    elif view_format == "json":
        return table_entry.to_json_response()

    else:
        raise Exception(f"Unknown 'format' GET arg given: {view_format}")


def table_search(request, table_name):
    raise NotImplementedError("Search view still under dev.")


def table_entry_new(request, table_name):

    component_class = _SAFE_COMPONENTS[table_name]
    context = {
        "component_name": component_class.component_name,
        "page_title": table_name,
        "page_title_icon": "mdi-database",
        "breadcrumbs": ["Data", table_name, "Form"],
    }
    template = getattr(
        component_class,
        "entry_form_template",
        "htmx/full_page_component.html",
    )
    return render(request, template, context)


def table_entry_new_many(request, table_name):
    # We can just use the entry-new view because our underlying htmx form
    # will dynamically determine the form mode using the URL path
    return table_entry_new(request, table_name)


def table_entry_update(request, table_name, table_entry_id):
    # We can just use the entry-new view because our underlying htmx form
    # will dynamically determine the form mode using the URL path
    return table_entry_new(request, table_name)
