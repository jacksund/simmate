
Displays a button in the frontend that when clicked calls a python method in the backend.

## Basic use

=== "frontend (html+django)"

    ``` html+django
    {% htmx_button method_name="my_method" %}
    ```

=== "backend (python)"

    ``` python
    from simmate.website.htmx.components import HtmxComponent

    class ExampleView(HtmxComponent):

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
        from simmate.website.htmx.components import HtmxComponent

        class ExampleView(HtmxComponent):
            my_input = "some default value"

            def my_method(self):
                self.my_input = "the button has been clicked!"
        ```

## Parameters

| Parameter         | Description                                                                                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `method_name`     | The name of the method to call in the backend. Use "submit" to trigger form submission.<br><small>*Type: `str`, Default: —*</small>                                                   |
| `label`           | The display label for the button. If not provided, the `method_name` may be used as the label.<br><small>*Type: `str`, Default: `None`*</small>                                       |
| `show_label`      | Whether to display the label text on the button.<br><small>*Type: `bool`, Default: `True`*</small>                                                                                    |
| `theme`           | CSS theme to use for coloring the button. Options are `primary`, `secondary`, `success`, `info`, `warning`, `danger`, and `dark`.<br><small>*Type: `str`, Default: `primary`*</small> |
| `icon`            | Name of the icon to place in the button. Choose from the [mdi catalog](https://pictogrammers.com/library/mdi/).<br><small>*Type: `str`, Default: `None`*</small>                      |
| `small`           | Whether to use a small button size.<br><small>*Type: `bool`, Default: `False`*</small>                                                                                                |
| `javascript_only` | If `True`, the button will only trigger javascript and not a backend call.<br><small>*Type: `bool`, Default: `False`*</small>                                                         |
| `include`         | CSS selector of elements to include in the request.<br><small>*Type: `str`, Default: `None`*</small>                                                                                  |
| `target`          | CSS selector of the element to swap the response into.<br><small>*Type: `str`, Default: `None`*</small>                                                                               |
| `grouped`         | Whether the button is part of a button group.<br><small>*Type: `bool`, Default: `False`*</small>                                                                                      |
