# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import ChemicalSystemSearch


class ChemicalSystemSearchTable(DynamicTableForm):
    table = ChemicalSystemSearch
    display_name = "Chemical System Searches"
    description_short = (
        "Evolutionary search results for discovering all stable phases within "
        " a chemical system (e.g., Fe-O). This workflow explores multiple "
        "compositions simultaneously to map out the thermodynamic convex hull."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "search": "core/base_data_types/structure_form.html",
    }

    enabled_forms = ["search"]
