# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import VariableNsitesCompositionSearch


class VariableNsitesCompositionSearchTable(DynamicTableForm):
    table = VariableNsitesCompositionSearch
    display_name = "Variable nSites Searches"
    description_short = (
        "Evolutionary search results for discovering the most stable crystal "
        "structure of a specific chemical formula across different unit cell "
        "sizes (number of sites). This workflow helps find the optimal "
        "supercell or primitive cell configuration."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "search": "core/base_data_types/structure_form.html",
    }

    enabled_forms = ["search"]
