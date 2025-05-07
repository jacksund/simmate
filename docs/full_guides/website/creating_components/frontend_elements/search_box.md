
Displays a search box widget that combines a selectbox (optional), a single-line text input, and a button. Useful for search/filter interfaces.

## Basic use

=== "frontend (html+django)"

    ```html+django
    {% load simmate_ui_tags %}

    {% search_box name="search_query" %}
    ```

=== "backend (python)"

    ```python
    from simmate.website.core_components.components import DynamicFormComponent

    class ExampleView(DynamicFormComponent):
        search_query = ""
    ```

## Parameters

| Parameter    | Description                                                                                                                               |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `name`       | The unique name or identifier for the text input field. Should match the backend attribute.<br><small>*Type: `str`, Default: —*</small>   |
| `label`      | The display label for the input. If not provided, a label is auto-generated from `name`.<br><small>*Type: `str`, Default: `None`*</small> |
| `show_label` | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                 |
| `help_text`  | Optional helper text shown alongside the input.<br><small>*Type: `str`, Default: `None`*</small>                                          |
| `disabled`   | If `True`, disables the input field.<br><small>*Type: `bool`, Default: `False`*</small>                                                   |

For the text input:

| Parameter     | Description                                                                                         |
| ------------- | --------------------------------------------------------------------------------------------------- |
| `placeholder` | Placeholder text for the input field.<br><small>*Type: `str`, Default: `"Type value..."`*</small>   |
| `max_length`  | Maximum number of characters allowed in the input.<br><small>*Type: `int`, Default: `None`*</small> |

For the selectbox:

| Parameter           | Description                                                                                                                                                                                                                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `show_selectbox`    | Whether to include a dropdown selectbox before the input.<br><small>*Type: `bool`, Default: `False`*</small>                                                                                                                                                                                       |
| `selectbox_name`    | Name/id for the selectbox. If not provided, auto-generated as `{name}_type`.<br><small>*Type: `str`, Default: `f"{name}_type"`*</small>                                                                                                                                                            |
| `selectbox_options` | The <u>name of the class attribute</u> that holds all options for the selectbox. In python, options should be a list of `('label', 'value')`, where `label` is what's shown in the UI and `value` is what is set in python.<br><small>*Type: `str`, Default: `f"{selectbox_name}_options"`</small> |

For the button:

| Parameter      | Description                                                                                                                   |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `button_name`  | The name/id for the button. If not provided, auto-generated as `set_{name}`.<br><small>*Type: `str`, Default: `None`*</small> |
| `button_theme` | Visual theme for the button (e.g., `"primary"`).<br><small>*Type: `str`, Default: `"primary"`*</small>                        |
| `button_icon`  | Icon name for the button.<br><small>*Type: `str`, Default: `"magnify"`*</small>                                               |
