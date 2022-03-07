# -*- coding: utf-8 -*-

# TODO: consider using workflow.result_table.__base__ (or __bases__) to
# determine which form mix-ins to use. Or alternatively use inspect.getrmo
# to get all subclasses (as DatabaseTable.from_toolkit does)

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import Serializer, HyperlinkedModelSerializer

from simmate.website.workflows import forms
from simmate.database.base_data_types import DatabaseTable


def get_form_from_table(table: DatabaseTable) -> forms.DatabaseTableForm:
    """
    Dynamically creates a Django Form from a Simmate database table.

    For example, this function would take
    `simmate.database.third_parties.MatProjStructure`
    and automatically make the following form:

    ``` python
    from django import forms
    from simmate.website.workflows import forms as simmate_forms


    class MatProjStrucureForm(
        forms.ModelForm,
        simmate_forms.Structure,
        simmate_forms.Thermodynamics,
    ):
        class Meta:
            model = MatProjStructure  # this is database table
            fields = "__all__"
            exclude = [""]  # this combines the exclude from Structure/Thermo mixins
    ```
    """

    # First we need to grab the parent mixin classes of the table. For example,
    # the MatProjStructure uses the database mixins ['Structure', 'Thermodynamics']
    # while MatProjStaticEnergy uses ["StaticEnergy"].
    mixin_names = [base.__name__ for base in table.__bases__]

    # Because our Forms follow the same naming conventions as
    # simmate.database.base_data_types, we can simply use these mixin names to
    # load a Form mixin from the simmate.website.workflows.form module. We add
    # these mixins onto the standard ModelForm class from django.
    form_mixins = [forms.DatabaseTableForm]
    form_mixins += [
        getattr(forms, name) for name in mixin_names if hasattr(forms, name)
    ]

    # The ModelForm mixin requires that we set extra fields in the Meta class.
    # We define those here. Note, we accept all fields by default and the
    # excluded fields are only those defined by the supported form_mixins -
    # and we skip the first mixin (which is always forms.ModelForm)
    class Meta:
        model = table
        fields = "__all__"
        exclude = [column for mixin in form_mixins[1:] for column in mixin.Meta.exclude]

    extra_attributes = {"Meta": Meta}
    # BUG: __module__ may need to be set in the future, but we never import
    # these forms elsewhere, so there's no need to set it now.

    # Now we dynamically create a new form class that we can return.
    NewClass = type(table.__name__, tuple(form_mixins), extra_attributes)

    return NewClass


class SimmateAPIView(GenericAPIView):
    # This class simply adds a method to enable passing extra context to the
    # final Response. This is only done when we are using the HTML format.

    extra_context: dict = {}
    """
    This defines extra context that should be passed to the template when
    using format=html. Note, you can have this as a constant or alternatively
    define a property. The only requirement is that a dictionary is returned.
    """

    def get_response(self, serializer: Serializer) -> Response:
        if self._format_kwarg == "html":
            data = {
                "serializer": serializer,  # consider adding queryset object
                "results": serializer.data,  # would it be better to use .initial_data?
                **self.extra_context,
            }
            return Response(data)
        else:
            return Response(serializer.data)


class ListAPIView(SimmateAPIView):
    """
    Concrete view for listing a queryset.
    """

    def get(self, request, *args, **kwargs):

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
        return self.get_response(serializer)


class RetrieveAPIView(SimmateAPIView):
    """
    Concrete view for retrieving a model instance.
    """

    def get(self, request, *args, **kwargs):

        # ---------------------------------------------------
        # This code is from the RetrieveModelMixin, where instead of returning
        # a response, we perform additional introspection first
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # return Response(serializer.data) <--- removed from original
        # ---------------------------------------------------
        return self.get_response(serializer)


def render_from_table(request, template: str, context, table: DatabaseTable):

    # For all tables, we share all the data -- no columns are hidden.
    class NewSerializer(HyperlinkedModelSerializer):
        class Meta:
            model = table
            fields = "__all__"

    # Querying each table varies though
    class NewViewSet(ListAPIView):
        queryset = table.objects.all()
        serializer_class = NewSerializer
        filterset_fields = ["id"]  # {"number": ["exact", "range"]}
        template_name = template
        extra_context = context

    # now pull together the html response
    response = NewViewSet.as_view()(request)
    return response
