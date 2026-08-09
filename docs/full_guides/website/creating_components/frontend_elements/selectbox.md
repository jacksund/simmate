
Displays a selectbox input widget and maps its value to the backend as a string.

We use [Select2](https://select2.org/) under the hood to make the dropdown searchable.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% htmx_selectbox name="my_input" %}
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

| Parameter            | Description                                                                                                                                                                                                                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`               | The unique name or identifier for the input field. This should match the name of your class attribute in the backend.<br><small>*Type: `str`, Default: —*</small>                                                                                                                            |
| `options`            | The <u>name of the class attribute</u> that holds all options for the dropdown menu. In python, options should be a list of `('label', 'value')`, where `label` is what's shown in the UI and `value` is what is set in python.<br><small>*Type: `str`, Default: `f"{name}_options"*</small> |
| `label`              | The display label for the input field. If not provided, the `name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                                                                                                                                                |
| `show_label`         | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                                                                                                                                                                    |
| `placeholder`        | The placeholder text to display when no option is selected.<br><small>*Type: `str`, Default: `"Select an option..."`*</small>                                                                                                                                                                |
| `help_text`          | Optional helper text to be shown alongside the input field.<br><small>*Type: `str`, Default: `None`*</small>                                                                                                                                                                                 |
| `dynamic_options`    | Whether the options list changes while the component is being updated. If your options are static, set this to `False` & add your options to `javascript_exclude` to improve performance.<br><small>*Type: `bool`, Default: `False`*</small>                                                 |
| `allow_custom_input` | Whether the user can type in their own value, in addition to the options listed.<br><small>*Type: `bool`, Default: `False`*</small>                                                                                                                                                          |
| `multiselect`        | Whether the user can select more than 1 option from the dropdown. When `True`, the python attribute for `name`  becomes a list of strings.<br><small>*Type: `bool`, Default: `False`*</small>                                                                                                |
| `defer`              | Whether to defer processing or submission of the input value.<br><small>*Type: `bool`, Default: `True`*</small>                                                                                                                                                                              |
| `method_name`        | The name of a backend method to call when the value changes. If set, `defer` is automatically set to `False`.<br><small>*Type: `str`, Default: `None`*</small>                                                                                                                               |
| `include`            | CSS selector of elements to include in the request.<br><small>*Type: `str`, Default: `None`*</small>                                                                                                                                                                                         |
