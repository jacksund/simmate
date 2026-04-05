# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import FixedCompositionSearch


class FixedCompositionSearchTable(DynamicTableForm):
    table = FixedCompositionSearch
    display_name = "Fixed-Composition Searches"
    description_short = (
        "Evolutionary search results for discovering the most stable crystal "
        "structure of a specific chemical formula. This workflow explores a "
        "wide range of symmetries and configurations to find the global "
        "energy minimum."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "search": "core/base_data_types/structure_form.html",
    }

    enabled_forms = ["search"]
