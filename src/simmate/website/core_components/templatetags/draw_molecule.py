# -*- coding: utf-8 -*-

import uuid

from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag
def draw_molecule(
    molecule: any,
    div_id: str = None,
    width: int = 150,
    height: int = 150,
):
    """
    Renders a molecule using Rdkit.js as SVG.

    Example use:
    ``` html
    {% load draw_molecule %}

    {% draw_molecule molecule %}
    {% draw_molecule molecule=example_var div_id="1234" width=400 height=400 %}
    ```
    """

    # TODO: auto scale width & height based on molecule size

    if not div_id:
        div_id = uuid.uuid4().hex

    # TODO: inspect mol type in case its a string
    # try:
    #     from simmate_corteva.toolkit import Molecule
    # except:
    #     Molecule = None
    # sdf_str = molecule.to_sdf()
    sdf_str = molecule.sdf_str  # assume Molecule db object for now

    context = {"div_id": div_id, "sdf_str": sdf_str, "width": width, "height": height}
    return render_to_string("rdkit/draw_molecule_image.html", context)
