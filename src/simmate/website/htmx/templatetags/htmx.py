# -*- coding: utf-8 -*-

import json

from django import template
from django.template.loader import render_to_string

from simmate.website.utilities import hash_options

from ..utilities import get_component

register = template.Library()


@register.inclusion_tag(filename="htmx/cdn.html")
def htmx_cdn_script():
    return  # html is static so no vars passed


@register.simple_tag(takes_context=True)
def htmx_component(context: dict, component_name: str, **kwargs):
    component_class = get_component(component_name)
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
    dynamically_set: bool = False,
    defer: bool = True,
    required: bool = False,
):
    """
    Display a single-line text input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    # grab the current value to render in the form
    component = context["component"]
    if name in context:
        current_value = context[name]
    elif hasattr(component, name):
        current_value = getattr(component, name)
    elif name in component.form_data:
        current_value = component.form_data[name]
    else:
        current_value = None

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
    options: list[str] = [],
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
    component = context["component"]

    if not label:
        label = name.replace("_", " ").title()
        if label.endswith(" Id"):
            label = label[:-3]
        elif label.endswith(" Ids"):
            label = label[:-4]

    if not options:
        default_name = f"{name}_options"
        if default_name in context:
            options = options = context[default_name]
        elif hasattr(component, default_name):
            options = getattr(component, default_name)
        elif default_name in component.form_data:
            options = component.form_data[default_name]
        elif hasattr(component, "table") and hasattr(
            getattr(component, "table"), default_name
        ):
            options = getattr(getattr(component, "table"), default_name)
        else:
            options = []

    if method_name:
        defer = False

    # grab the initial value to render in the form
    if name in context:
        initial_value = context[name]
    elif hasattr(component, name):
        initial_value = getattr(component, name)
    elif name in component.form_data:
        initial_value = component.form_data[name]
    else:
        initial_value = None

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


# -----------------------------------------------------------------------------

# TODO

# @register.inclusion_tag(
#     filename="core_components/input_elements/file_upload.html",
#     takes_context=True,
# )
# def file_upload(
#     context: dict,
#     name: str,
#     label: str = None,
#     show_label: bool = True,
#     help_text: str = None,
#     max_size: int = 10,  # in MB
#     disabled: bool = False,
#     defer: bool = False,
#     file_type: str = ".csv",  # only accept CSV files. Comma sep for others
# ):
#     """
#     Display a file upload widget.
#     """
#     if not label:
#         label = name.replace("_", " ").title()

#     return locals()


# @register.inclusion_tag(
#     filename="core_components/input_elements/molecule_input.html",
#     takes_context=True,
# )
# def molecule_input(
#     context: dict,
#     name: str = "molecule",
#     label: str = None,
#     show_label: bool = True,
#     help_text: str = None,
#     load_button: bool = True,
#     set_molecule_method: str = None,
#     allow_sketcher_input: bool = True,
#     sketcher_input_label: str = "Draw Molecule",
#     # Mol text input (text_area)
#     allow_text_input: bool = False,
#     text_input_name: str = None,
#     text_input_label: str = "Paste Molecule Text",
#     # Custom input (text_input)
#     allow_custom_input: bool = False,
#     custom_input_name: str = None,
#     custom_input_label: str = "Custom Input",
#     custom_input_placeholder: str = "12345",
#     # TODO:
#     # initial_value: bool = None,
#     many_molecules: bool = False,
# ):
#     """
#     Display a ChemDraw.js (or ChemDoodle.js) input widget.
#     """
#     if not label:
#         label = name.replace("_", " ").title()

#     if not set_molecule_method:
#         set_molecule_method = (
#             f"set_{name}" if not many_molecules else "load_many_molecules"
#         )

#     if allow_text_input and not text_input_name:
#         text_input_name = f"{name}_text_input"

#     if allow_custom_input and not custom_input_name:
#         custom_input_name = f"{name}_custom_input"

#     show_option_labels = (
#         True
#         if [allow_sketcher_input, allow_text_input, allow_custom_input].count(True) > 1
#         else False
#     )
#     if show_option_labels:
#         noption = 1
#         if allow_custom_input:
#             custom_input_label = f"Option {noption}: {custom_input_label}"
#             noption += 1
#         if allow_text_input:
#             text_input_label = f"Option {noption}: {text_input_label}"
#             noption += 1
#         if allow_sketcher_input:
#             sketcher_input_label = f"Option {noption}: {sketcher_input_label}"
#             noption += 1

#     molecule = context[name]
#     molecule_matches = context["molecule_matches"]

#     return locals()


# @register.inclusion_tag(
#     filename="core_components/input_elements/search_box.html",
#     takes_context=True,
# )
# def search_box(
#     context: dict,
#     name: str,  # text input
#     label: str = None,
#     show_label: bool = True,
#     help_text: str = None,
#     placeholder: str = "Type value...",
#     max_length: int = None,
#     disabled: bool = False,
#     # for button
#     button_name: str = None,
#     button_theme: str = "primary",
#     button_icon: str = "magnify",
#     # for selectbox
#     show_selectbox: bool = False,
#     selectbox_name: str = None,
#     selectbox_options: list = None,
# ):
#     """
#     Display a input group that includes a drop down menu (optional),
#     a text input, and a button all together.
#     """
#     if not label:
#         label = name.replace("_", " ").title()

#     if show_selectbox and not selectbox_name:
#         selectbox_name = f"{name}_type"

#     if show_selectbox and not selectbox_options:
#         selectbox_options = context.get(f"{selectbox_name}_options", [])

#     if not button_name:
#         button_name = f"set_{name}"

#     return locals()
