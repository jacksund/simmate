# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.database.base_data_types import Thermodynamics as ThermodynamicsTable


class Thermodynamics(filters.FilterSet):
    class Meta:
        model = ThermodynamicsTable
        fields = dict(
            energy=["range"],
            energy_per_atom=["range"],
            energy_above_hull=["range"],
            is_stable=["exact"],
            formation_energy=["range"],
            formation_energy_per_atom=["range"],
        )
