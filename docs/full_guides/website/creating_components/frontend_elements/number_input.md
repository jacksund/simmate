
Displays a numeric input widget and maps its value to the backend as either a `float` or `int`.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% load simmate_ui_tags %}

    {% number_input name="my_input" %}
    ```

=== "backend (python)"

    ``` python
    from simmate.website.core_components.components import DynamicFormComponent

    class ExampleView(DynamicFormComponent):
        my_input = 1234
 
    ```

## Parameters

| Parameter     | Description                                                                                                                                                       |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`        | The unique name or identifier for the input field. This should match the name of your class attribute in the backend.<br><small>*Type: `str`, Default: —*</small> |
| `label`       | The display label for the input field. If not provided, the `name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                     |
| `show_label`  | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                                         |
| `help_text`   | Optional helper text to be shown alongside the input field.<br><small>*Type: `str`, Default: `None`*</small>                                                      |
| `placeholder` | The placeholder text to display when input field is empty.<br><small>*Type: `str`, Default: `"Enter details..."`*</small>                                         |
| `maximum`     | Maximum value allowed to be entered by user. `None` means no limit. <br><small>*Type: `float`, Default: `None`*</small>                                           |
| `minimum`     | Minimum value allowed to be entered by user. `None` means no limit. <br><small>*Type: `float`, Default: `None`*</small>                                           |
| `is_int`      | Whether the input is an integer (set to `True`) or a float (set to `False`). <br><small>*Type: `bool`, Default: `False`*</small>                                  |
| `step_size`   | Descrete step size of the number. `None` means it is a continuos float value with no limit on digits. <br><small>*Type: `int`, Default: `None`*</small>           |
| `defer`       | Whether to defer processing or submission of the input value.<br><small>*Type: `bool`, Default: `True`*</small>                                                   |
