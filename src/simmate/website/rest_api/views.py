# -*- coding: utf-8 -*-

from django.contrib.auth.models import User, Group

from rest_framework import viewsets
from rest_framework import permissions

from simmate.website.rest_api.serializers import (
    UserSerializer,
    GroupSerializer,
    MaterialsProjectSerializer,
    JarvisSerializer,
    AflowSerializer,
    OqmdSerializer,
    CodSerializer,
)

from simmate.database.third_parties.all import (
    MaterialsProjectStructure,
    JarvisStructure,
    AflowStructure,
    OqmdStructure,
    CodStructure,
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.order_by("-date_joined").all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]


class MaterialsProjectViewSet(viewsets.ModelViewSet):
    queryset = MaterialsProjectStructure.objects.all()
    serializer_class = MaterialsProjectSerializer
    filterset_fields = "__all__"

class JarvisViewSet(viewsets.ModelViewSet):
    queryset = JarvisStructure.objects.all()
    serializer_class = JarvisSerializer
    filterset_fields = "__all__"
    
class AflowViewSet(viewsets.ModelViewSet):
    queryset = AflowStructure.objects.all()
    serializer_class = AflowSerializer
    filterset_fields = "__all__"
    
class OqmdViewSet(viewsets.ModelViewSet):
    queryset = OqmdStructure.objects.all()
    serializer_class = OqmdSerializer
    filterset_fields = "__all__"

class CodViewSet(viewsets.ModelViewSet):
    queryset = CodStructure.objects.all()
    serializer_class = CodSerializer
    filterset_fields = "__all__"
