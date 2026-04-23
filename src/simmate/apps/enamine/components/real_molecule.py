# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import MoleculeInput

from ..models import EnamineRealMolecule


class EnamineRealMoleculeComponent(TableComponent, MoleculeInput):
    table = EnamineRealMolecule
    display_name = "Enamine REAL"
    description_short = (
        "The Enamine REAL (REadily Accessible) database contains billions of "
        "accessible compounds that can be synthesized quickly using established "
        "chemical reactions. It is a premier resource for large-scale "
        "virtual screening."
    )
    template_names = {
        "search": "core/base_data_types/molecule_form.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]
