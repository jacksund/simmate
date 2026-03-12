
Displays a checkbox input widget and maps its value to the backend as a boolean.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% htmx_checkbox name="my_input" %}
    ```

=== "backend (python)"

    ``` python
    from simmate.website.htmx.components import HtmxComponent

    class ExampleView(HtmxComponent):
        my_input = "some default value"
 
    ```

## Parameters

| Parameter     | Description                                                                                                                                                       |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`        | The unique name or identifier for the input field. This should match the name of your class attribute in the backend.<br><small>*Type: `str`, Default: —*</small> |
| `label`       | The display label for the input field. If not provided, the `name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                     |
| `show_label`  | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                                         |
| `help_text`   | Optional helper text to be shown alongside the input field.<br><small>*Type: `str`, Default: `None`*</small>                                                      |
| `side_text`   | Text displayed to the right of the checkbox.<br><small>*Type: `str`, Default: `Yes/True`*</small>                                                                 |
| `defer`       | Whether to defer processing or submission of the input value.<br><small>*Type: `bool`, Default: `True`*</small>                                                   |
| `required`    | Whether the field is required for form submission.<br><small>*Type: `bool`, Default: `False`*</small>                                                             |
| `switch_mode` | Whether to display the checkbox as a toggle switch.<br><small>*Type: `bool`, Default: `True`*</small>                                                              |
