# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..symmetry import Spacegroup


class SpacegroupTable(DynamicTableForm):
    table = Spacegroup
    display_name = "Symmetry Spacegroups"
    description_short = (
        "Mathematical descriptions of the symmetry present in crystalline "
        "materials. Spacegroups categorize structures into 230 unique types "
        "based on their translational and point symmetry operations."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "workflow_explorer/static_energy/table.html",
        "entry": "workflow_explorer/static_energy/view.html",
    }
