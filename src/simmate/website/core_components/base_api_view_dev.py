# -*- coding: utf-8 -*-

from django.views import View

from django.shortcuts import render
from simmate.website.utilities import get_pagination_urls

from simmate_corteva.discovery_lab.models import CortevaTarget


# class SimmateApiViewDEV(View):
#     # get --> decides if list or entry, then calls one of...
#     #   get_about_reponse (docs)
#     #   get_list_response (filtered table using GET args)
#     #   get_entry_response (single row using ID)


class DatabaseTableView(View):

    def get(self, request):
        # move to proper view function based on requested format
        view_format = request.GET.get("format", "html")
        if view_format == "html":
            return self.get_html_view(request)
        elif view_format == "json":
            return self.get_json_view(request)
        elif view_format == "api":
            return self.get_api_view(request)
        else:
            raise Exception(f"Unknown 'format' GET arg given: {view_format}")

    def get_json_view(self, request):
        page = CortevaTarget.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        response = page.object_list.to_json_response(
            next_url=pagination_urls["next"],
            previous_url=pagination_urls["previous"],
        )
        return response

    def get_api_view(self, request):
        page = CortevaTarget.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        breakpoint()

    def get_html_view(self, request):
        page = CortevaTarget.filter_from_request(request)
        pagination_urls = get_pagination_urls(request, page)
        context = {
            "page_title": "The Discovery Lab App",
            "breadcrumbs": [("data_explorer:home", "Data")],
            "breadcrumb_active": CortevaTarget.table_name,
            "table": CortevaTarget,
            "page": page,
            "pagination_urls": pagination_urls,
            # "paginator": page.paginator,
            # "entries": page.object_list,  # page.paginator.object_list gives ALL results
            # extra optional unicorn views (link to db model?)
            "quick_search_view": "cortevatarget-search",
            "updater_view": "cortevatarget-update-many",
            "add_new_view": 123,  # TODO: switch to view
        }
        # template = "data_explorer_dev/table.html"
        template = "discovery_lab/cortevatarget_full.html"
        return render(request, template, context)
    
    # -------------------------------------------------------------------------
    
    # def _get_breadcrumb_context(self):
    #     pass

# {
#     "count": 3292,
#     "next": "http://simmate.kf.research.corteva.com/data/CortevaTarget/?format=api&page=2",
#     "previous": null,
#     "results": [ ... ]
# }

# data = {
#     "filterset": filterset,
#     "filterset_mixins": filterset._meta.model.get_mixin_names(),
#     "form": filterset.form,
#     "extra_filters": filterset._meta.model.api_filters_extra,
#     "calculations": serializer.instance,  # return python objs, not dict
#     # OPTIMIZE: counting can take ~20 sec for ~10 mil rows, which is
#     # terrible for a web UI. I tried a series of fixes but no luck:
#     #   https://stackoverflow.com/questions/55018986/
#     "ncalculations_matching": queryset.count(),
#     # "ncalculations_possible": self.get_queryset().count(), # too slow
#     **self.paginator.get_html_context(),
#     **self.get_list_context(request, **kwargs),
# }
