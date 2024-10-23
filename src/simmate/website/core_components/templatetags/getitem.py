# -*- coding: utf-8 -*-

# Copied code from...
# https://stackoverflow.com/questions/32157995/
# This link is helpful if we want to update this tag...
# https://stackoverflow.com/questions/844746/

from django import template

register = template.Library()


@register.filter
def getitem(dictionary, key):
    """
    Wraps the get dictionary python method into a django template tag so that we
    can dynamically grab items.

    Example use:
    ``` html
    {% load getitem %}
    {{ my_dict|getitem:example_key }}
    ```
    """
    return dictionary.get(key)
