# -*- coding: utf-8 -*-


import uuid

from django import template

from simmate.apps.rdkit.models import Molecule as DatabaseMolecule
from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.website.utilities import hash_options

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
    placeholder: str = "Enter value...",
    max_length: int = None,
    disabled: bool = False,
    defer: bool = True,
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
    defer: bool = True,
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
    placeholder: str = None,
    maximum: float | int = None,
    minimum: float | int = None,
    is_int: bool = False,
    step_size: float | int = None,
    defer: bool = True,
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
    defer: bool = True,
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
    small: bool = False,
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
    dynamic_options: bool = False,
    allow_custom_input: bool = False,
    multiselect: bool = False,
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

    initial_value = context.get(name, None)

    # Needed because select2 is within an "ignore" div but we also want to
    # replace the full select box if the options are changed at all
    if dynamic_options:
        options_hash = hash_options(options)

    return locals()


@register.inclusion_tag(
    filename="core_components/input_elements/radio.html",
    takes_context=True,
)
def radio(
    context: dict,
    name: str,
    options: list[tuple[any, str]] = [],
    label: str = None,
    show_label: bool = True,
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
    filename="core_components/input_elements/molecule_input.html",
    takes_context=True,
)
def molecule_input(
    context: dict,
    name: str = "molecule",
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    load_button: bool = True,
    set_molecule_method: str = None,
    allow_sketcher_input: bool = True,
    sketcher_input_label: str = "Draw Molecule",
    # Mol text input (text_area)
    allow_text_input: bool = False,
    text_input_name: str = None,
    text_input_label: str = "Paste Molecule Text",
    # Custom input (text_input)
    allow_custom_input: bool = False,
    custom_input_name: str = None,
    custom_input_label: str = "Custom Input",
    custom_input_placeholder: str = "12345",
    # TODO:
    # initial_value: bool = None,
    many_molecules: bool = False,
):
    """
    Display a ChemDraw.js (or ChemDoodle.js) input widget.
    """
    if not label:
        label = name.replace("_", " ").title()

    if not set_molecule_method:
        set_molecule_method = (
            f"set_{name}" if not many_molecules else "load_many_molecules"
        )

    if allow_text_input and not text_input_name:
        text_input_name = f"{name}_text_input"

    if allow_custom_input and not custom_input_name:
        custom_input_name = f"{name}_custom_input"

    show_option_labels = (
        True
        if [allow_sketcher_input, allow_text_input, allow_custom_input].count(True) > 1
        else False
    )
    if show_option_labels:
        noption = 1
        if allow_custom_input:
            custom_input_label = f"Option {noption}: {custom_input_label}"
            noption += 1
        if allow_text_input:
            text_input_label = f"Option {noption}: {text_input_label}"
            noption += 1
        if allow_sketcher_input:
            sketcher_input_label = f"Option {noption}: {sketcher_input_label}"
            noption += 1

    molecule = context[name]
    molecule_matches = context["molecule_matches"]

    return locals()


@register.inclusion_tag(
    filename="core_components/input_elements/search_box.html",
    takes_context=True,
)
def search_box(
    context: dict,
    name: str,  # text input
    label: str = None,
    show_label: bool = True,
    help_text: str = None,
    placeholder: str = "Type value...",
    max_length: int = None,
    disabled: bool = False,
    # for button
    button_name: str = None,
    button_theme: str = "primary",
    button_icon: str = "magnify",
    # for selectbox
    show_selectbox: bool = False,
    selectbox_name: str = None,
    selectbox_options: list = None,
):
    """
    Display a input group that includes a drop down menu (optional),
    a text input, and a button all together.
    """
    if not label:
        label = name.replace("_", " ").title()

    if show_selectbox and not selectbox_name:
        selectbox_name = f"{name}_type"

    if show_selectbox and not selectbox_options:
        selectbox_options = context.get(f"{selectbox_name}_options", [])

    if not button_name:
        button_name = f"set_{name}"

    return locals()


# -----------------------------------------------------------------------------

# basic elements (non-unicorn)


@register.inclusion_tag(
    filename="core_components/basic_elements/alert.html",
    takes_context=True,
)
def alert(
    context: dict,
    message: str,
    theme: str = "primary",
    label: str = None,
    icon: str = None,
):
    """
    Display a alert widget with some message.
    """
    default_icon_mapping = {
        "primary": "information",
        "info": "information",
        "secondary": "information",
        "warning": "alert",
        "danger": "alert",
    }
    if not icon:
        icon = default_icon_mapping.get(theme, "information")

    return locals()


@register.inclusion_tag(
    filename="core_components/basic_elements/draw_molecule.html",
    takes_context=True,
)
def draw_molecule(
    context: dict,
    molecule: any,
    div_id: str = None,
    width: int = 150,
    height: int = 150,
):
    """
    Draw a molecule using Rdkit.js.
    """

    # TODO: auto scale width & height based on molecule size

    # javascript requires unique ids
    if not div_id:
        div_id = uuid.uuid4().hex

    # see what kind of molecule we were given and get its sdf string
    if isinstance(molecule, DatabaseMolecule):
        molecule = molecule.sdf_str
    elif isinstance(molecule, ToolkitMolecule):
        molecule = molecule.to_sdf().replace("\n", "\\n")
    else:
        # !!! Should I try from_dynamic? or just assume its a string that rdkitjs can read?
        molecule = molecule.replace("\n", "\\n")

    return locals()


@register.inclusion_tag(
    filename="core_components/basic_elements/canvas.html",
    takes_context=True,
)
def canvas(
    context: dict,
    name: str,
    width: int = 150,
    height: int = 150,
):
    """
    Place a canvas that will later be used to draw something, such as a
    molecule using Rdkit.js.

    This is separate from the `draw_molecule` tag because the JS call comes from
    the DynamicFormComponent dynamically & *after* the page is loaded.
    """
    return locals()
