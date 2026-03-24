# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

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
