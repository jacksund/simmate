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
    Display a checkbox widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    return locals()


@register.inclusion_tag(
    filename="core_components/input_elements/button.html",
    takes_context=True,
)
def button(
    context: dict,
    name: str,  # fxn_to_call
    label: str = None,
    show_label: bool = True,
    theme: str = "primary",
    icon: str = None,
):
    """
    Display a button widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    return locals()


@register.inclusion_tag(
    filename="core_components/input_elements/selectbox.html",
    takes_context=True,
)
def selectbox(
    context: dict,
    name: str,
    options: list[tuple[any, str]] = [],
    label: str = None,
    show_label: bool = True,
    initial_value: bool = None,
    dynamic_options: bool = False,
    allow_custom_input: bool = False,
):
    """
    Display a checkbox widget.
    """
    # options should be a list of tuples: (value, display)

    if not label:
        label = name.replace("_", " ").title()

    if not options:
        options = context.get(f"{name}_options", [])

    if not initial_value:
        initial_value = context.get(name)

    # Needed because select2 is within an "ignore" div but we also want to
    # replace the full select box if the options are changed at all
    if dynamic_options:
        options_hash = hash_options(options)

    return locals()


def hash_options(options: list[tuple]) -> str:
    # for speed, we only hash the keys, which are shorter and should be
    # consistent with all their values anyways
    return str(hash(";".join([str(k) for k, _ in options])))
