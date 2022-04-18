# -*- coding: utf-8 -*-

from django.http import HttpRequest

from rest_framework.viewsets import GenericViewSet

# from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from simmate.website.core_components.filters import DatabaseTableFilter
from simmate.database.base_data_types import DatabaseTable


class SimmateAPIViewSet(GenericViewSet):
    """
    Example use:

    ``` python
    # in views.py
    class ExampleTableViewSet(SimmateAPIViewSet):
        table = ExampleTable
        template_list = "custom_app/list.html"
        template_retrieve = "custom_app/retrieve.html"

    # in urls.py
    path(
        route="example-table",
        view=ExampleTableViewSet.list_view,
        name="example-list",
    )
    path(
        route="example-table/<int:id>",
        view=ExampleTableViewSet.retrieve_view,
        name="example-retrieve",
    )
    ```
    """

    table: DatabaseTable = None

    template_list: str = None

    template_retrieve: str = None

    def get_list_response(self, request: HttpRequest, *args, **kwargs) -> Response:

        # This code is modified from the ListModelMixin, where instead of returning
        # a response, we perform additional introspection first.
        # https://github.com/encode/django-rest-framework/blob/master/rest_framework/mixins.py#L33

        # self.format_kwarg --> not sure why this always returns None, so I
        # grab the format from the request instead. If it isn't listed, then
        # I'm using the default which is html.
        self._format_kwarg = request.GET.get("format", "html")

        queryset = self.filter_queryset(self.get_queryset())

        # attempt to paginate the results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        # If don't have the html format, we follow simple logic from the
        # original ListModelMixin method
        if self._format_kwarg != "html":
            if page is not None:
                return self.get_paginated_response(serializer.data)
            else:
                return Response(serializer.data)

        # otherwise we assume the html format.
        else:
            filterset = self.filterset_class(request.GET)
            data = {
                # "filterset": filterset, # not used at the momemnt
                "filterset_mixins": filterset.get_mixin_names(),
                "form": filterset.form,
                "extra_filters": filterset.get_extra_filters(),
                "calculations": serializer.instance,  # return python objs, not dict
                "ncalculations_matching": queryset.count(),
                "ncalculations_possible": self.get_queryset().count(),
                **self.paginator.get_html_context(),
                **self.get_list_context(request, **kwargs),
            }
            return Response(data)

    def get_retrieve_response(self, request: HttpRequest, *args, **kwargs) -> Response:

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
                **self.get_retrieve_context(request, **kwargs),
            }
            return Response(data)
        else:
            return Response(serializer.data)

    @classmethod
    def from_table(
        cls,
        table: DatabaseTable,
        view_type: str,
        **kwargs,
    ):
        # For all tables, we share all the data -- no columns are hidden. Therefore
        # the code for the Serializer is always the same.
        class NewSerializer(ModelSerializer):
            class Meta:
                model = table
                fields = "__all__"

        # Build the filter from our base class using default settings
        NewFilterSet = DatabaseTableFilter.from_table(table)

        # For the source dataset, not all tables have a "created_at" column, but
        # when they do, we want to return results with the most recent additions first
        # by default. Ordering can also be overwritten by passing "ordering=..."
        # to the URL.
        default_ordering_field = (
            "-created_at" if hasattr(table, "created_at") else table._meta.pk.name
        )

        # we also want to preload spacegroup for the structure mixin
        intial_queryset = table.objects.all()
        if hasattr(table, "spacegroup"):
            intial_queryset = intial_queryset.select_related("spacegroup")

        NewViewSet = type(
            f"{table.__name__}ViewSet",
            (cls,),
            dict(
                queryset=intial_queryset,
                serializer_class=NewSerializer,
                filterset_class=NewFilterSet,
                ordering_fields="__all__",  # allowed to order by any field
                ordering=[default_ordering_field],  # set default order
                **kwargs,
            ),
        )

        # these two parameters depend on the view_type
        if view_type == "list":
            NewViewSet.template_name = cls.template_list
            return NewViewSet.as_view({"get": "get_list_response"})
        elif view_type == "retrieve":
            NewViewSet.template_name = cls.template_retrieve
            return NewViewSet.as_view({"get": "get_retrieve_response"})
        else:
            raise Exception("Unknown view type. Must be 'list' or 'retrieve'.")

    # -------------------------------------------------------------------------

    # METHODS FOR STATIC VIEWS

    @classmethod
    def list_view(cls, request, **request_kwargs):
        view = cls.from_table(table=cls.table, view_type="list")
        return view(request, **request_kwargs)

    @classmethod
    def retrieve_view(cls, request, **request_kwargs):
        view = cls.from_table(table=cls.table, view_type="retrieve")
        return view(request, **request_kwargs)

    # -------------------------------------------------------------------------

    # METHODS FOR DYNAMIC VIEWS

    # NOTE: These dynamically create a serializer and a view EVERY TIME a
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
    #   2. making all APIViews up-

    def get_table(self, request: HttpRequest, *args, **kwargs) -> Response:
        if not self.table:
            raise NotImplementedError()
        else:
            return self.table

    @classmethod
    def dynamic_list_view(cls, request, **request_kwargs):
        table = cls.get_table(request, **request_kwargs)
        view = cls.from_table(table=table, view_type="list")
        return view(request, **request_kwargs)

    @classmethod
    def dynamic_retrieve_view(cls, request, **request_kwargs):
        table = cls.get_table(request, **request_kwargs)
        view = cls.from_table(table=table, view_type="retrieve")
        return view(request, **request_kwargs)

    # -------------------------------------------------------------------------

    # OPTIONAL METHODS FOR SUPPLYING EXTRA CONTEXT TO HTML TEMPLATES

    def get_list_context(self, request, **request_kwargs) -> dict:
        """
        This defines extra context that should be passed to the template when
        using format=html when a list-view is requested. By default, no extra
        context is returned.
        """
        return {}

    def get_retrieve_context(self, request, **request_kwargs) -> dict:
        """
        This defines extra context that should be passed to the template when
        using format=html when a retrieve-view is requested. By default, no extra
        context is returned.
        """
        return {}
