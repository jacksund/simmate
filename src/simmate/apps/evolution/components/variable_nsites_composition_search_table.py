# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

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
