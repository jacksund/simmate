# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import FixedCompositionSearch


class FixedCompositionSearchComponent(TableComponent):
    table = FixedCompositionSearch
    display_name = "Fixed-Composition Searches"
    description_short = (
        "Evolutionary search results for discovering the most stable crystal "
        "structure of a specific chemical formula. This workflow explores a "
        "wide range of symmetries and configurations to find the global "
        "energy minimum."
    )
    template_names = {
        "search": "core/base_data_types/structure_form.html",
        "entries": "evolution/fixed_composition_search/table.html",
        "entry": "evolution/fixed_composition_search/view.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]
