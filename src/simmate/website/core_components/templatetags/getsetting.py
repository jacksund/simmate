# -*- coding: utf-8 -*-
"""
Copied code from...
https://stackoverflow.com/questions/433162/
"""

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def getsetting(name):
    """
    Loads the value of a given django (or simmate) setting

    Example use:
    ``` html
    {% load getsetting %}
    {% getsetting "LANGUAGE_CODE" %}
    ```
    """
    return getattr(settings, name, "")
