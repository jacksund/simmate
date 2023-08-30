# -*- coding: utf-8 -*-

from django import template

register = template.Library()


@register.filter
def sdfdoodle(obj):
    """
    Converts an sdf string to one that can be passed to the doodle_molecule fxn

    Example use:
    ``` html
    {% load sdfdoodle %}
    {{ my_object|sdfdoodle }}
    ```
    """
    return obj.replace("\n", "\\n")
