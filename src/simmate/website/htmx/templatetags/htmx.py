# -*- coding: utf-8 -*-

import json

from django import template
from django.template.loader import render_to_string

from simmate.website.utilities import hash_options

from ..component import HtmxComponent

register = template.Library()


@register.inclusion_tag(filename="htmx/cdn.html")
def htmx_cdn_script():
    return  # html is static so no vars passed


@register.simple_tag(takes_context=True)
def htmx_component(context: dict, component_name: str, **kwargs):
    # TODO: util that converts name to class
    if component_name == "ExampleComponent":
        component_class = HtmxComponent
    else:
        raise NotImplementedError()

    component = component_class(context=context, **kwargs)
    return render_to_string(
        template_name=component.template_name,
        context=component.get_context(),
    )


@register.inclusion_tag("htmx/js_actions.html")
def htmx_js_actions(actions):
    return {"actions": json.dumps(actions)}


@register.inclusion_tag(filename="htmx/loading_spinner.html")
def htmx_loading_spinner():
    return  # html is static so no vars passed


# -----------------------------------------------------------------------------


@register.inclusion_tag(
    filename="htmx/input_elements/text_input.html",
    takes_context=True,
)
def htmx_text_input(
    context: dict,
    name: str,
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    placeholder: str = "Enter value...",
    max_length: int = None,
    disabled: bool = False,
    defer: bool = True,
    required: bool = False,
):
    """
    Display a single-line text input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    return locals()


@register.inclusion_tag(
    filename="htmx/input_elements/text_area.html",
    takes_context=True,
)
def htmx_text_area(
    context: dict,
    name: str,
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    placeholder: str = "Enter details...",
    ncols: int = 30,
    nrows: int = 4,
    defer: bool = True,
    required: bool = False,
):
    """
    Display a multi-line text input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    return locals()


@register.inclusion_tag(
    filename="htmx/input_elements/number_input.html",
    takes_context=True,
)
def htmx_number_input(
    context: dict,
    name: str,
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    placeholder: str = None,
    maximum: float | int = None,
    minimum: float | int = None,
    is_int: bool = False,
    step_size: float | int = None,
    defer: bool = True,
    required: bool = False,
):
    """
    Display a numeric input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    if not step_size:
        step_size = 1 if is_int else "any"

    if not placeholder:
        placeholder = "123" if is_int else "0.123"

    return locals()


@register.inclusion_tag(
    filename="htmx/input_elements/checkbox.html",
    takes_context=True,
)
def htmx_checkbox(
    context: dict,
    name: str,
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    side_text: str = "Yes/True",
    defer: bool = True,
    required: bool = False,
):
    """
    Display a checkbox widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    return locals()


@register.inclusion_tag(
    filename="htmx/input_elements/radio.html",
    takes_context=True,
)
def htmx_radio(
    context: dict,
    name: str,
    options: list[tuple[any, str]] = [],
    label: str = None,
    show_label: bool = True,
    defer: bool = True,
    required: bool = False,
):
    """
    Display a radio select widget.
    """
    # options should be a list of tuples: (value, display)

    if not label:
        label = name.replace("_", " ").title()

    if not options:
        options = context.get(f"{name}_options", [])

    initial_value = context.get(name, None)

    return locals()


@register.inclusion_tag(
    filename="htmx/input_elements/selectbox.html",
    takes_context=True,
)
def htmx_selectbox(
    context: dict,
    name: str,
    options: list[tuple[any, str]] = [],
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    dynamic_options: bool = False,
    allow_custom_input: bool = False,
    multiselect: bool = False,
    defer: bool = True,
    method_name: str = None,  # fxn_to_call -- presumes defer=False
):
    """
    Display a selectbox widget.
    """
    # options should be a list of tuples: (value, display)

    if not label:
        label = name.replace("_", " ").title()
        if label.endswith(" Id"):
            label = label[:-3]
        elif label.endswith(" Ids"):
            label = label[:-4]

    if not options:
        options = context.get(f"{name}_options", [])

    if method_name:
        defer = False

    initial_value = context.get(name, None)

    # Needed because select2 is within an "ignore" div but we also want to
    # replace the full select box if the options are changed at all
    if dynamic_options:
        options_hash = hash_options(options)

    # BUG-FIX
    # the searchbar breaks when the dropdown is in a model or offcanvas. So
    # this must be set to patch that via the `data-dropdown-parent` attr
    # popout_parent_id = {
    #     "searchpopout": "offcanvasQuickSearch",
    #     "updatemanypopout": "offcanvasUpdater",
    #     "createpopout": "offcanvasAddEntry",
    # }.get(context["component"].component_id, None)

    return locals()


@register.inclusion_tag(
    filename="htmx/input_elements/button.html",
    takes_context=True,
)
def htmx_button(
    context: dict,
    method_name: str,  # fxn_to_call. "submit" is special case
    label: str = None,
    show_label: bool = True,
    theme: str = "primary",
    icon: str = None,
    small: bool = False,
    javascript_only: bool = False,
):
    """
    Display a button widget.
    """
    if not label:
        label = method_name.replace("_", " ").title()

    return locals()
