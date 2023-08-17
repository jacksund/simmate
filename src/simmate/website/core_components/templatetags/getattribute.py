# -*- coding: utf-8 -*-

# Copied code from...
# https://stackoverflow.com/questions/32157995/
# This link is helpful if we want to update this tag...
# https://stackoverflow.com/questions/844746/

from django import template

register = template.Library()


@register.filter
def getattribute(obj, attr):
    """
    Wraps the getattr python method into a django template tag so that we
    can dynamically grab object properties.

    Example use:
    ``` html
    {% load getattribute %}
    {{ my_object|getattribute:example_var }}
    ```

    Note `example_var` in the example above is a string set to a property name.
    """
    try:
        return getattr(obj, attr)
    except:  # RelatedObjectDoesNotExist
        return None
