# -*- coding: utf-8 -*-

# TODO: consider using workflow.result_table.__base__ (or __bases__) to
# determine which form mix-ins to use. Or alternatively use inspect.getrmo
# to get all subclasses (as DatabaseTable.from_toolkit does)

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
