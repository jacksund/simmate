# -*- coding: utf-8 -*-


import uuid

from django import template

from simmate.apps.rdkit.models import Molecule as DatabaseMolecule
from simmate.toolkit import Molecule as ToolkitMolecule

register = template.Library()


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
    small: bool = False,
):
    """
    Display a alert widget with some message.
    """
    default_icon_mapping = {
        "primary": "info-circle-fill",
        "info": "info-circle-fill",
        "success": "check-circle-fill",
        "secondary": "info-circle-fill",
        "warning": "exclamation-triangle-fill",
        "danger": "exclamation-triangle-fill",
    }
    if not icon:
        icon = default_icon_mapping.get(theme, "info-circle-fill")

    return locals()


@register.inclusion_tag(
    filename="core_components/chem_elements/draw_molecule.html",
    takes_context=True,
)
def draw_molecule(
    context: dict,
    molecule: DatabaseMolecule | ToolkitMolecule,
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


@register.inclusion_tag(
    filename="core_components/basic_elements/foreign_key_link.html",
    takes_context=True,
)
def foreign_key_link(
    context: dict,
    entry,  # db_object
    display_column: str = None,
    mode: str = "text",  # other options are "pill" and "block"
    truncate_chars: int = "inf",
    open_in_new: bool = False,
):
    return locals()


@register.inclusion_tag(
    filename="core_components/basic_elements/update_entry_link.html",
    takes_context=True,
)
def update_entry_link(
    context: dict,
    entry,  # db_object
):
    return locals()


@register.inclusion_tag(
    filename="core_components/basic_elements/status_bar.html",
    takes_context=True,
)
def status_bar(
    context: dict,
    status: str,
    theme: str = "info",
):
    return locals()


@register.inclusion_tag(
    filename="core_components/basic_elements/table_header.html",
    takes_context=True,
)
def table_header(
    context: dict,
    column_name: str,
    text_display: str = None,
    min_width: int = None,  # in px
):
    order_by = context.request.GET.get("order_by", "-id")

    if order_by.startswith("-"):
        order_by = order_by[1:]
        reverse = True
    else:
        reverse = False

    if order_by == column_name:
        if reverse:
            arrow = "up"
            link = f"{column_name}"
        else:
            arrow = "down"
            link = f"-{column_name}"
    else:
        link = f"{column_name}"

    if not text_display:
        text_display = column_name.replace("_", " ").title()

    request = context.request  # BUG-FIX
    return locals()


@register.inclusion_tag(
    filename="core_components/basic_elements/button_link.html",
    takes_context=True,
)
def button_link(
    context: dict,
    link: str,
    label: str = None,
    small: bool = False,
    icon: str = "open-in-new",
    theme: str = "primary",
    open_in_new: bool = False,
):
    return locals()
