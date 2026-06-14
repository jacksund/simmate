# -*- coding: utf-8 -*-

from simmate.database.mixins.symmetry import Spacegroup
from simmate.website.data_explorer.components import TableComponent


class SpacegroupComponent(TableComponent):
    table = Spacegroup
    display_name = "Symmetry Spacegroups"
    description_short = (
        "Mathematical descriptions of the symmetry present in crystalline "
        "materials. Spacegroups categorize structures into 230 unique types "
        "based on their translational and point symmetry operations."
    )
    template_names = {
        "entries": "workflow_explorer/static_energy/table.html",
        "entry": "workflow_explorer/static_energy/view.html",
    }
