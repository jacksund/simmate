# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.utilities import get_chemical_subsystems
from simmate.database.base_data_types import Structure as StructureTable


class Structure(filters.FilterSet):
    class Meta:
        model = StructureTable
        fields = dict(
            nsites=["range"],
            nelements=["range"],
            # elements=["contains"],
            density=["range"],
            density_atomic=["range"],
            volume=["range"],
            volume_molar=["range"],
            formula_full=["exact"],
            formula_reduced=["exact"],
            formula_anonymous=["exact"],
            spacegroup__number=["exact"],
            spacegroup__symbol=["exact"],
            spacegroup__crystal_system=["exact"],
            spacegroup__point_group=["exact"],
        )

    include_subsystems = filters.BooleanFilter(
        field_name="include_subsystems",
        label="Include chemical subsystems in results?",
        method="skip_filter",
    )
    """
    Whether to include subsystems of the given `chemical_system`. For example,
    the subsystems of Y-C-F would be Y, C, F, Y-C, Y-F, etc..
    """

    # include_suprasystems = forms.BooleanField(label="Include Subsytems", required=False)
    # TODO: Supra-systems would include all the elements listed AND more. For example,
    # searching Y-C-F would also return Y-C-F-Br, Y-Sc-C-F, etc.

    chemical_system = filters.CharFilter(method="filter_chemical_system")
    """
    The chemical system of the structure (e.g. "Y-C-F" or "Na-Cl")
    """

    def skip_filter(self, queryset, name, value):
        """
        For filter fields that use this method, nothing is done to queryset. This
        is because the filter is typically used within another field. For example,
        the `include_subsystems` field is not applied to the queryset, but it
        is used within the `filter_chemical_system` method.
        """
        return queryset

    def filter_chemical_system(self, queryset, name, value):
        # name/value here are the key/value pair for chemical system

        # Grab the "include_subsystems" field from the filter form. Note, this
        # value will be given as a string which we convert to a python boolean
        include_subsystems = self.data.dict().get("include_subsystems", "false")
        include_subsystems = True if include_subsystems == "true" else False

        # TODO:
        # Make sure that the chemical system is made of valid elements and
        # separated by hyphens

        # check if the user wants subsystems included (This will be True or False)
        if include_subsystems:
            systems_cleaned = get_chemical_subsystems(value)

        # otherwise just clean the single system
        else:
            # Convert the system to a list of elements
            systems_cleaned = value.split("-")
            # now recombine the list back into alphabetical order
            systems_cleaned = ["-".join(sorted(systems_cleaned))]
            # NOTE: we call this "systems_cleaned" and put it in a list so
            # that our other methods don't have to deal with multiple cases
            # when running a django filter.

        filtered_queryset = queryset.filter(chemical_system__in=systems_cleaned)

        # now return the cleaned value. Note that this is now a list of
        # chemical systems, where all elements are in alphabetical order.
        return filtered_queryset
