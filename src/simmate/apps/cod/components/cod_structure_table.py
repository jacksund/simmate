# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import CodStructure


class CodStructureTable(DynamicTableForm):
    table = CodStructure
    display_name = "COD"
    description_short = (
        "The Crystallography Open Database (COD) is an open-access collection "
        "of crystal structures for organic, inorganic, metal-organic compounds, "
        "and minerals. It serves as a primary resource for experimental "
        "diffraction data."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "cod/structures/table.html",
        "entry": "cod/structures/view.html",
    }
