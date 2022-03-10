# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.database.base_data_types import Spacegroup as SpacegroupTable


class Spacegroup(filters.FilterSet):
    class Meta:
        model = SpacegroupTable
        fields = dict(
            number=["exact", "range"],
            symbol=["exact"],
            crystal_system=["exact"],
            point_group=["exact"],
        )
