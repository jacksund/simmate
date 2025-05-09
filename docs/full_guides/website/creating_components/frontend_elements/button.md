
Displays a button in the frontend that when clicked calls a python method in the backend.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% button name="my_method" %}
    ```

=== "backend (python)"

    ``` python
    from simmate.website.core_components.components import DynamicFormComponent

    class ExampleView(DynamicFormComponent):

        def my_method(self):
            # ...
            # run any python code
            # ...
            return  # nothing is done w. return values
 
    ```

    !!! tip
        You methods can access and even update other attributes. 
        
        For example, a `text_input` named `my_input` can be updated via:
        ``` python
        from simmate.website.core_components.components import DynamicFormComponent

        class ExampleView(DynamicFormComponent):
            my_input = "some default value"

            def my_method(self):
                self.my_input = "the button has been clicked!"
        ```

## Parameters

| Parameter    | Description                                                                                                                                                                           |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`       | The name of the method to call in the backend.<br><small>*Type: `str`, Default: —*</small>                                                                                            |
| `label`      | The display label for the input field. If not provided, the `name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                                         |
| `show_label` | Whether to display the label alongside the input field.<br><small>*Type: `bool`, Default: `True`*</small>                                                                             |
| `theme`      | CSS theme to use for coloring the button. Options are `primary`, `secondary`, `success`, `info`, `warning`, `danger`, and `dark`.<br><small>*Type: `str`, Default: `primary`*</small> |
| `icon`       | Name of the icon to place in the button. Choose from the [mdi catalog](https://pictogrammers.com/library/mdi/).<br><small>*Type: `str`, Default: `None`*</small>                      |
| `small`      | The maximum number of characters allowed in the input field.<br><small>*Type: `int`, Default: `None`*</small>                                                                         |
