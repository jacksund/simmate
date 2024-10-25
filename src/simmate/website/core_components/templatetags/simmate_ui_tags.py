# -*- coding: utf-8 -*-

from django import template

register = template.Library()

# The naming convention for our tags and kwargs mostly are based on Streamlit inputs:
#   https://docs.streamlit.io/develop/api-reference/widgets


@register.inclusion_tag(
    filename="core_components/input_elements/text_input.html",
    takes_context=True,
)
def text_input(
    context: dict,
    name: str,
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    placeholder: str = "Type value...",
    max_length: int = None,
):
    """
    Display a single-line text input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    return locals()


@register.inclusion_tag(
    filename="core_components/input_elements/text_area.html",
    takes_context=True,
)
def text_area(
    context: dict,
    name: str,
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    placeholder: str = "Enter details...",
    ncols: int = 30,
    nrows: int = 4,
):
    """
    Display a multi-line text input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    return locals()


@register.inclusion_tag(
    filename="core_components/input_elements/number_input.html",
    takes_context=True,
)
def number_input(
    context: dict,
    name: str,
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    placeholder: str = "0.123",
    maximum: float | int = None,
    minimum: float | int = None,
    is_int: bool = False,
    step_size: float | int = None,
):
    """
    Display a numeric input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    if not step_size:
        step_size = 1 if is_int else "any"

    return locals()


@register.inclusion_tag(
    filename="core_components/input_elements/checkbox.html",
    takes_context=True,
)
def checkbox(
    context: dict,
    name: str,
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    side_text: str = "Yes/True",
):
    """
    Display a numeric input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    return locals()
