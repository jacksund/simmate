
Displays a radio select input widget and maps its value to the backend as a string.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% htmx_radio name="my_input" %}
    ```

=== "backend (python)"

    ``` python
    from simmate.website.htmx.components import HtmxComponent

    class ExampleView(HtmxComponent):

        my_input = None

        my_input_options = [
            ("label1", "value1"),
            ("label2", "value2"),
            ("label3", "value3"),
            # ...
        ]

    ```

## Parameters

| Parameter    | Description                                                                                                                                                                                                                                                                                  |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`       | The unique name or identifier for the input field. This should match the name of your class attribute in the backend.<br><small>*Type: `str`, Default: —*</small>                                                                                                                            |
| `options`    | The <u>name of the class attribute</u> that holds all options for the dropdown menu. In python, options should be a list of `('label', 'value')`, where `label` is what's shown in the UI and `value` is what is set in python.<br><small>*Type: `str`, Default: `f"{name}_options"*</small> |
| `label`      | The display label for the input field. If not provided, the `name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                                                                                                                                                |
| `show_label` | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                                                                                                                                                                    |
| `defer`      | Whether to defer processing or submission of the input value.<br><small>*Type: `bool`, Default: `True`*</small>                                                                                                                                                                              |
| `required`   | Whether the field is required for form submission.<br><small>*Type: `bool`, Default: `False`*</small>                                                                                                                                                                                        |

