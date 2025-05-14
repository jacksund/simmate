
Displays a single-line text input widget and maps its value to the backend as a string.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% text_input name="my_input" %}
    ```

=== "backend (python)"

    ``` python
    from simmate.website.core_components.components import DynamicFormComponent

    class ExampleView(DynamicFormComponent):
        my_input = "some default value"
 
    ```

## Parameters

| Parameter     | Description                                                                                                                                                       |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`        | The unique name or identifier for the input field. This should match the name of your class attribute in the backend.<br><small>*Type: `str`, Default: —*</small> |
| `label`       | The display label for the input field. If not provided, the `name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                     |
| `show_label`  | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                                         |
| `help_text`   | Optional helper text to be shown alongside the input field.<br><small>*Type: `str`, Default: `None`*</small>                                                      |
| `placeholder` | The placeholder text to display when input field is empty.<br><small>*Type: `str`, Default: `"Type value..."`*</small>                                            |
| `max_length`  | The maximum number of characters allowed in the input field.<br><small>*Type: `int`, Default: `None`*</small>                                                     |
| `disabled`    | If `True`, the input field will be rendered as disabled and not editable.<br><small>*Type: `bool`, Default: `False`*</small>                                      |
| `defer`       | Whether to defer processing or submission of the input value.<br><small>*Type: `bool`, Default: `True`*</small>                                                   |
