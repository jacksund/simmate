
Displays a molecule sketcher widget and maps its value to the backend as a string + `toolkit.Molecule` object.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% load simmate_ui_tags %}

    {% molecule_input %}
    ```

=== "backend (python)"

    ``` python
    from simmate.website.core_components.components import (
        DynamicFormComponent,
        MoleculeInput,
    )


    class CortevaTargetFormView(DynamicFormComponent, MoleculeInput):

        class Meta:
            javascript_exclude = (
                *DynamicFormComponent.Meta.javascript_exclude,
                *MoleculeInput.Meta.javascript_exclude,
            )
 
    ```

## Parameters

| Parameter             | Description                                                                                                                                                                   |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                | The unique name or identifier for the input field. This should match the name of your class attribute in the backend.<br><small>*Type: `str`, Default: —*</small>             |
| `label`               | The display label for the input field. If not provided, the `name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                                 |
| `show_label`          | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                                                     |
| `help_text`           | Optional helper text to be shown alongside the input field.<br><small>*Type: `str`, Default: `None`*</small>                                                                  |
| `load_button`         | Whether to display a button that loads the molecule from the sketcher and the replaces the sketcher with the molecule image.<br><small>*Type: `str`, Default: `None`*</small> |
| `set_molecule_method` | Name of the method that parses the molecule and sets the python class attribute.<br><small>*Type: `str`, Default: `None`*</small>                                             |
| `many_molecules`      | Whether to allow input of multiple molecules (e.g., as a list or batch input).<br><small>*Type: `bool`, Default: `False`*</small>                                             |

For the molecule sketcher:

| Parameter              | Description                                                                                                |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| `allow_sketcher_input` | Whether to allow molecule input via a sketcher widget.<br><small>*Type: `bool`, Default: `True`*</small>   |
| `sketcher_input_label` | The label to display above the sketcher input.<br><small>*Type: `str`, Default: `"Draw Molecule"`*</small> |

For the text input area:

| Parameter          | Description                                                                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allow_text_input` | Whether to allow molecule input via a text area (e.g., SMILES, mol block).<br><small>*Type: `bool`, Default: `False`*</small>                           |
| `text_input_name`  | The unique name or identifier for the text input field. If not provided, defaults to `name` + `_text`.<br><small>*Type: `str`, Default: `None`*</small> |
| `text_input_label` | The label to display above the text input area.<br><small>*Type: `str`, Default: `"Paste Molecule Text"`*</small>                                       |

For the "custom input" area (e.g., IDs from other table):

| Parameter                  | Description                                                                                                                                                 |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allow_custom_input`       | Whether to allow a custom input field (e.g., for IDs or external references).<br><small>*Type: `bool`, Default: `False`*</small>                            |
| `custom_input_name`        | The unique name or identifier for the custom input field. If not provided, defaults to `name` + `_custom`.<br><small>*Type: `str`, Default: `None`*</small> |
| `custom_input_label`       | The label to display above the custom input field.<br><small>*Type: `str`, Default: `"Custom Input"`*</small>                                               |
| `custom_input_placeholder` | Placeholder text for the custom input field.<br><small>*Type: `str`, Default: `"12345"`*</small>                                                            |
