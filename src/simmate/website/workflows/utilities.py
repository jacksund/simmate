# -*- coding: utf-8 -*-

from django.http import HttpRequest

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from simmate.website.workflows.filters import DatabaseTableFilter
from simmate.database.base_data_types import DatabaseTable


class SimmateAPIView(GenericAPIView):
    # This class simply adds a method to enable passing extra context to the
    # final Response. This is only done when we are using the HTML format.

    extra_context: dict = {}
    """
    This defines extra context that should be passed to the template when
    using format=html. Note, you can have this as a constant or alternatively
    define a property. The only requirement is that a dictionary is returned.
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> Response:
        if self.viewset_type == "list":
            return self.list_view(request, *args, **kwargs)
        elif self.viewset_type == "retrieve":
            return self.retrieve_view(request, *args, **kwargs)

    def list_view(self, request: HttpRequest, *args, **kwargs) -> Response:

        # self.format_kwarg --> not sure why this always returns None, so I
        # grab the format from the request instead. If it isn't listed, then
        # I'm using the default which is html.
        self._format_kwarg = request.GET.get("format", "html")

        # ---------------------------------------------------
        # This code is from the ListModelMixin, where instead of returning
        # a response, we perform additional introspection first. I turn off
        # pagination for now but need to revisit this.
        queryset = self.filter_queryset(self.get_queryset())
        if self._format_kwarg != "html":  # <--- added this condition
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        # return Response(serializer.data)  <--- removed from original
        # ---------------------------------------------------

        if self._format_kwarg == "html":
            filterset = self.filterset_class(request.GET)
            data = {
                # "filterset": filterset, # not used at the momemnt
                "filterset_mixins": filterset.get_mixin_names(),
                "form": filterset.form,
                "extra_filters": filterset.get_extra_filters(),
                "calculations": serializer.instance,  # return python objs, not dict
                "ncalculations_possible": self.get_queryset().count(),
                **self.extra_context,
            }
            return Response(data)
        else:
            return Response(serializer.data)

    def retrieve_view(self, request: HttpRequest, *args, **kwargs) -> Response:

        # self.format_kwarg --> not sure why this always returns None, so I
        # grab the format from the request instead. If it isn't listed, then
        # I'm using the default which is html.
        self._format_kwarg = request.GET.get("format", "html")

        # ---------------------------------------------------
        # This code is from the RetrieveModelMixin, where instead of returning
        # a response, we perform additional introspection first
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # return Response(serializer.data) <--- removed from original
        # ---------------------------------------------------

        if self._format_kwarg == "html":
            # we want to return a python object, not a serialized dictionary
            # because the object has more attributes and methods attached to it.
            calculation = serializer.instance
            data = {
                "calculation": calculation,
                "table_mixins": calculation.get_mixin_names(),
                "extra_columns": calculation.get_extra_columns(),
                **self.extra_context,
            }
            return Response(data)
        else:
            return Response(serializer.data)


def render_from_table(
    request: HttpRequest,
    template: str,
    context: dict,
    table: DatabaseTable,
    view_type: str,
    request_kwargs: dict = {},
) -> Response:

    # NOTE: This dynamically creates a serializer and a view EVERY TIME a
    # URL is requested. This means...
    #   1. there is no pre-set api that exists. The exisiting api must be inferred
    #       from lower level workflows and their tables
    #   2. these views will be very inefficient if queried by a script
    # I chose dynamic creation over creating all endpoints on-startup to prevent
    # the `from simmate.database import connect` method from taking too long --
    # as that would require import all workflows on start-up. However, if the
    # (1) api spec or (2) speed of this method ever becomes an issue, I can
    # address these by either...
    #   1. having a utility that prints out the full API spec but isn't called on startup
    #   2. making all APIViews up-front

    # For all tables, we share all the data -- no columns are hidden. Therefore
    # the code for the Serializer is always the same.
    # !!! consider switching to HyperlinkedModelSerializer
    class NewSerializer(ModelSerializer):
        class Meta:
            model = table
            fields = "__all__"

    NewFilterSet = DatabaseTableFilter.from_table(table)

    # for the source dataset, not all tables have a "created_at" column, but
    # when they do, we want to return results with the most recent additions first
    if hasattr(table, "created_at"):
        intial_queryset = table.objects.order_by("-created_at").all()
    else:
        intial_queryset = table.objects.order_by("id").all()
    # we also want to preload spacegroup for the structure mixin
    if hasattr(table, "spacegroup"):
        intial_queryset = intial_queryset.select_related("spacegroup")

    # TODO: consider using the following to dynamically name these classes
    #   NewClass = type(table.__name__, mixins, extra_attributes)
    class NewViewSet(SimmateAPIView):
        # we show the most recent calculations first
        queryset = intial_queryset
        serializer_class = NewSerializer
        template_name = template
        extra_context = context
        filterset_class = NewFilterSet
        viewset_type = view_type  # BUG: view_type = view_type throws an error
        # These two are only used for the view_type = "retrieve"
        lookup_url_kwarg = "workflow_run_id"
        lookup_field = "id"

    # now pull together the html response
    response = NewViewSet.as_view()(request, **request_kwargs)
    return response
