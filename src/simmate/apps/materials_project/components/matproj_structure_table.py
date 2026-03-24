# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import MatprojStructure


class MatprojStructureTable(DynamicTableForm):
    table = MatprojStructure
    display_name = "Materials Project"
    description_short = (
        "Computed properties of all known inorganic materials, provided by the "
        "Materials Project at Berkeley National Labs. This is one of the most "
        "widely used databases for thermodynamic stability and electronic "
        "property screening."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "materials_project/structures/table.html",
        "entry": "materials_project/structures/view.html",
    }
