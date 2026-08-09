
Displays a molecule sketcher widget and maps its value to the backend as a string + `toolkit.Molecule` object.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% htmx_molecule_input %}
    ```

=== "backend (python)"

    ``` python
    from simmate.website.htmx.components import (
        HtmxComponent,
        MoleculeInput,
    )


    class TargetFormView(HtmxComponent, MoleculeInput):

        class Meta:
            javascript_exclude = (
                *HtmxComponent.Meta.javascript_exclude,
                *MoleculeInput.Meta.javascript_exclude,
            )
 
    ```

## Parameters

| Parameter        | Description                                                                                                                                                                   |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`           | The unique name or identifier for the input field. This should match the name of your class attribute in the backend.<br><small>*Type: `str`, Default: `"molecule"`*</small>  |
| `label`          | The display label for the input field. If not provided, the `name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                                 |
| `show_label`     | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                                                     |
| `help_text`      | Optional helper text to be shown alongside the input field.<br><small>*Type: `str`, Default: `None`*</small>                                                                  |
| `load_button`    | Whether to display a button that loads the molecule from the sketcher and the replaces the sketcher with the molecule image.<br><small>*Type: `bool`, Default: `True`*</small> |
| `defer`          | Whether to defer processing or submission of the input value.<br><small>*Type: `bool`, Default: `True`*</small>                                                               |
| `many_molecules` | Whether to allow input of multiple molecules (e.g., as a list or batch input).<br><small>*Type: `bool`, Default: `False`*</small>                                             |
| `export_format`  | The format to export the molecule as. Options are `mol` and `smiles`.<br><small>*Type: `str`, Default: `"mol"`*</small>                                                       |

For the molecule sketcher:

| Parameter              | Description                                                                                                |
| ---------------------- | ---------------------------------------------------------------------------------------------------------- |
| `allow_sketcher_input` | Whether to allow molecule input via a sketcher widget.<br><small>*Type: `bool`, Default: `True`*</small>   |
| `sketcher_input_label` | The label to display above the sketcher input.<br><small>*Type: `str`, Default: `"Draw Molecule"`*</small> |

For the text input area:

| Parameter          | Description                                                                                                                                   |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `allow_text_input` | Whether to allow molecule input via a text area (e.g., SMILES, mol block).<br><small>*Type: `bool`, Default: `False`*</small>                 |
| `text_input_label` | The label to display above the text input area.<br><small>*Type: `str`, Default: `"Paste Molecule Text"`*</small>                             |

For the reference input area:

| Parameter                     | Description                                                                                                                   |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `allow_reference_input`       | Whether to allow molecule input via a reference ID (e.g. PubChem CID).<br><small>*Type: `bool`, Default: `False`*</small>     |
| `reference_input_label`       | The label to display above the reference input field.<br><small>*Type: `str`, Default: `"Molecule Ref. ID"`*</small>          |
| `reference_input_placeholder` | Placeholder text for the reference input field.<br><small>*Type: `str`, Default: `"12345"`*</small>                           |

For the "custom input" area (e.g., IDs from other table):

| Parameter                  | Description                                                                                                                 |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `allow_custom_input`       | Whether to allow a custom input field (e.g., for IDs or external references).<br><small>*Type: `bool`, Default: `False`*</small> |
| `custom_input_label`       | The label to display above the custom input field.<br><small>*Type: `str`, Default: `"Custom Input"`*</small>               |
| `custom_input_placeholder` | Placeholder text for the custom input field.<br><small>*Type: `str`, Default: `"12345"`*</small>                             |
