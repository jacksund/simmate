# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import StructureInput

from ..models import CodStructure


class CodStructureComponent(TableComponent, StructureInput):
    table = CodStructure
    display_name = "COD"
    description_short = (
        "The Crystallography Open Database (COD) is an open-access collection "
        "of crystal structures for organic, inorganic, metal-organic compounds, "
        "and minerals. It serves as a primary resource for experimental "
        "diffraction data."
    )
    template_names = {
        "search": "cod/structures/form.html",
        "entries": "cod/structures/table.html",
        "entry": "cod/structures/view.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]
