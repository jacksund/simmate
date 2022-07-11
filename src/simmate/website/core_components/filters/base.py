# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from simmate.database.base_data_types import DatabaseTable


class DatabaseTableFilter(filters.FilterSet):
    class Meta:
        table = DatabaseTable
        fields = {}

    @classmethod
    def get_mixins(cls):
        """
        Grabs the mix-in Forms that were used to make this class. This will
        be mix-ins like Structure, Forces, etc. from the
        `simmate.website.workflows.forms` module.
        """
        # We skip the first entry because it is always DatabaseTableForm
        return [parent_class for parent_class in cls.__bases__[1:]]

    @classmethod
    def get_mixin_names(cls):
        return [mixin.__name__ for mixin in cls.get_mixins()]

    @classmethod
    def get_extra_filters(cls):
        """
        Finds all columns that aren't covered by the supported Form mix-ins.

        For example, a form made from the database table...

        ``` python
        from simmate.database.base_data_types import (
            table_column,
            Structure,
            Forces,
        )

        class ExampleTable(Structure, Forces):
            custom_column1 = table_column.FloatField()
            custom_column2 = table_column.FloatField()
        ```

        ... would return ...

        ``` python
        ["custom_column1", "custom_column2"]
        ```
        """

        all_columns = cls.base_filters.keys()
        columns_w_mixin = [
            column for mixin in cls.get_mixins() for column in mixin.base_filters.keys()
        ]
        extra_columns = [
            column
            for column in all_columns
            if column not in columns_w_mixin and column != "id"
        ]
        return extra_columns

    @classmethod
    def from_table(cls, table: DatabaseTable):
        """
        Dynamically creates a Django Filter from a Simmate database table.

        For example, this function would take
        `simmate.database.third_parties.MatprojStructure`
        and automatically make the following filter:

        ``` python
        from simmate.website.core_components.filters import (
            DatabaseTableFilter,
            Structure,
            Thermodynamics,
        )


        class MatprojStrucureFilter(
            DatabaseTableFilter,
            Structure,
            Thermodynamics,
        ):
            class Meta:
                model = MatprojStructure  # this is database table
                fields = {...} # this combines the fields from Structure/Thermo mixins

            # These attributes are set using the declared filters from Structure/Thermo mixins
            declared_filter1 = ...
            declared_filter1 = ...
        ```
        """

        # this must be imported locally because it depends on all other classes
        # from this module -- and will create circular import issues if outside
        from simmate.website.core_components import filters as simmate_filters

        # First we need to grab the parent mixin classes of the table. For example,
        # the MatprojStructure uses the database mixins ['Structure', 'Thermodynamics']
        # while MatprojStaticEnergy uses ["StaticEnergy"].
        mixin_names = [base.__name__ for base in table.__bases__]

        # Because our Forms follow the same naming conventions as
        # simmate.database.base_data_types, we can simply use these mixin names to
        # load a Form mixin from the simmate.website.workflows.form module. We add
        # these mixins onto the standard ModelForm class from django.
        filter_mixins = [cls]
        filter_mixins += [
            getattr(simmate_filters, name)
            for name in mixin_names
            if hasattr(simmate_filters, name)
        ]

        # combine the fields of each filter mixin. Note we use .get_fields instead
        # of .fields to ensure we get a dictionary back
        filter_fields = {
            field: conditions
            for mixin in filter_mixins
            for field, conditions in mixin.get_fields().items()
        }

        # Also combine all declared filters from each mixin
        filters_declared = {
            name: filter_obj
            for mixin in filter_mixins
            for name, filter_obj in mixin.declared_filters.items()
        }

        # The FilterSet class requires that we set extra fields in the Meta class.
        # We define those here. Note, we accept all fields by default and the
        # excluded fields are only those defined by the supported form_mixins -
        # and we skip the first mixin (which is always DatabaseTableFilter)
        class Meta:
            model = table
            fields = filter_fields

        extra_attributes = {"Meta": Meta, **filters_declared}
        # BUG: __module__ may need to be set in the future, but we never import
        # these forms elsewhere, so there's no need to set it now.

        # Now we dynamically create a new form class that we can return.
        NewClass = type(table.__name__, tuple(filter_mixins), extra_attributes)

        return NewClass
