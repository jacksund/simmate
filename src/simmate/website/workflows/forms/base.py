# -*- coding: utf-8 -*-

from django import forms


class DatabaseTableForm(forms.ModelForm):
    class Meta:
        fields = "__all__"
        exclude = ["source"]

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
    def get_extra_columns(cls):
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

        all_columns = cls.base_fields.keys()
        columns_w_mixin = [
            column for mixin in cls.get_mixins() for column in mixin.base_fields.keys()
        ]
        extra_columns = [
            column
            for column in all_columns
            if column not in columns_w_mixin and column != "id"
        ]
        return extra_columns
