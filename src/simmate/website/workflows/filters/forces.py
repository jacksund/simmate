# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.database.base_data_types import Forces as ForcesTable


class Forces(filters.FilterSet):
    class Meta:
        model = ForcesTable
        fields = dict(
            site_force_norm_max=["range"],
            site_forces_norm_per_atom=["range"],
            lattice_stress_norm=["range"],
            lattice_stress_norm_per_atom=["range"],
        )
