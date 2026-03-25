# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import ChemicalSystemSearch


class ChemicalSystemSearchTable(DynamicTableForm):
    table = ChemicalSystemSearch
    display_name = "Chemical System Searches"
    description_short = (
        "Evolutionary search results for discovering all stable phases within "
        " a chemical system (e.g., Fe-O). This workflow explores multiple "
        "compositions simultaneously to map out the thermodynamic convex hull."
    )
