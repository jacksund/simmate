# -*- coding: utf-8 -*-

from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from simmate.database.base_data_types import Spacegroup
from simmate.database.third_parties import (
    AflowStructure,
    CodStructure,
    JarvisStructure,
    MatProjStructure,
    OqmdStructure,
)


"""

Instead of making an individual view for each model and each of its properties,
we instead let djangorestframework do the heavy lifting for us -- it creates
all views for us via a "Serializer" and "ViewSet". So this is a two-step process
for each model. Here is an example:

from some.package.models import MyExampleModel    

class MyExampleSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = MyExampleStructure
        fields = "__all__"    

class MyExampleViewSet(ReadOnlyModelViewSet):
    queryset = MyExampleModel.objects.all()
    serializer_class = MyExampleSerializer
    filterset_fields = "__all__"

"""

# --------------------------------------------------------------------------------------


class SpacegroupSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Spacegroup
        fields = "__all__"


class SpacegroupViewSet(ReadOnlyModelViewSet):
    queryset = Spacegroup.objects.order_by("number").all()
    serializer_class = SpacegroupSerializer
    filterset_fields = "__all__"


# --------------------------------------------------------------------------------------


class MatProjSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = MatProjStructure
        fields = "__all__"


class MatProjViewSet(ReadOnlyModelViewSet):
    queryset = MatProjStructure.objects.all()
    serializer_class = MatProjSerializer
    filterset_fields = "__all__"


# --------------------------------------------------------------------------------------


class JarvisSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = JarvisStructure
        fields = "__all__"


class JarvisViewSet(ReadOnlyModelViewSet):
    queryset = JarvisStructure.objects.all()
    serializer_class = JarvisSerializer
    filterset_fields = "__all__"


# --------------------------------------------------------------------------------------


class AflowSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = AflowStructure
        fields = "__all__"


class AflowViewSet(ReadOnlyModelViewSet):
    queryset = AflowStructure.objects.all()
    serializer_class = AflowSerializer
    filterset_fields = "__all__"


# --------------------------------------------------------------------------------------


class OqmdSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = OqmdStructure
        fields = "__all__"


class OqmdViewSet(ReadOnlyModelViewSet):
    queryset = OqmdStructure.objects.all()
    serializer_class = OqmdSerializer
    filterset_fields = "__all__"


# --------------------------------------------------------------------------------------


class CodSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = CodStructure
        fields = "__all__"


class CodViewSet(ReadOnlyModelViewSet):
    queryset = CodStructure.objects.all()
    serializer_class = CodSerializer
    filterset_fields = "__all__"


# --------------------------------------------------------------------------------------
