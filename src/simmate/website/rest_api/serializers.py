# -*- coding: utf-8 -*-

from django.contrib.auth.models import User, Group

from rest_framework import serializers

from simmate.database.third_parties.all import (
    MaterialsProjectStructure,
    JarvisStructure,
    AflowStructure,
    OqmdStructure,
    CodStructure,
)

# --------------------------------------------------------------------------------------

# Currently, django REST doesn't allow us to set all fields to read-only. So
# instead of writing out all fields for each, we want these set to read-only
# automatically.
# Once this meta field is supported, we can remove this base class:
#   read_only_fields = "__all__"


class ReadOnlySerializer(serializers.HyperlinkedModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields


# --------------------------------------------------------------------------------------

# These serializers are for admins-only and provide a good example for how
# to set up a serializer normally.


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]
        read_only_fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]
        read_only_fields = ["url", "name"]


# --------------------------------------------------------------------------------------


class MaterialsProjectSerializer(ReadOnlySerializer):
    class Meta:
        model = MaterialsProjectStructure
        fields = "__all__"


class JarvisSerializer(ReadOnlySerializer):
    class Meta:
        model = JarvisStructure
        fields = "__all__"


class AflowSerializer(ReadOnlySerializer):
    class Meta:
        model = AflowStructure
        fields = "__all__"


class OqmdSerializer(ReadOnlySerializer):
    class Meta:
        model = OqmdStructure
        fields = "__all__"


class CodSerializer(ReadOnlySerializer):
    class Meta:
        model = CodStructure
        fields = "__all__"
