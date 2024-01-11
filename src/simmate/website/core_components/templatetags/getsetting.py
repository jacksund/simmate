# -*- coding: utf-8 -*-
"""
Copied code from...
https://stackoverflow.com/questions/433162/
"""

from django import template
from django.conf import settings as django_settings

from simmate.configuration import settings as simmate_settings

register = template.Library()


@register.simple_tag
def django_setting(name):
    """
    Loads the value of a django setting

    Example use:
    ``` html
    {% load getsetting %}
    {% django_setting "DEBUG" %}
    ```
    """

    return getattr(django_settings, name, "")


@register.simple_tag
def simmate_setting(name):
    """
    Loads the value of a simmate setting

    Example use:
    ``` html
    {% load getsetting %}
    {% simmate_setting "website.require_login" %}
    ```
    """
    keys = name.split(".")
    assert len(keys) > 1  # ensure correct usage
    final_value = simmate_settings  # start with the full object
    for key in keys:  # recursively grab attributes
        final_value = getattr(final_value, key, "")
    return final_value
