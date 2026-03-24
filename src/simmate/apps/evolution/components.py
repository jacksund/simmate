# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from .models import (
    FixedCompositionSearch,
    VariableNsitesCompositionSearch,
    ChemicalSystemSearch,
    SteadystateSource,
)


class FixedCompositionSearchTable(DynamicTableForm):
    table = FixedCompositionSearch
    html_display_name = "Fixed-Composition Searches"
    html_description_short = (
        "Evolutionary search results for discovering the most stable crystal "
        "structure of a specific chemical formula. This workflow explores a "
        "wide range of symmetries and configurations to find the global "
        "energy minimum."
    )


class VariableNsitesCompositionSearchTable(DynamicTableForm):
    table = VariableNsitesCompositionSearch
    html_display_name = "Variable nSites Searches"
    html_description_short = (
        "Evolutionary search results for discovering the most stable crystal "
        "structure of a specific chemical formula across different unit cell "
        "sizes (number of sites). This workflow helps find the optimal "
        "supercell or primitive cell configuration."
    )


class ChemicalSystemSearchTable(DynamicTableForm):
    table = ChemicalSystemSearch
    html_display_name = "Chemical System Searches"
    html_description_short = (
        "Evolutionary search results for discovering all stable phases within "
        " a chemical system (e.g., Fe-O). This workflow explores multiple "
        "compositions simultaneously to map out the thermodynamic convex hull."
    )


class SteadystateSourceTable(DynamicTableForm):
    table = SteadystateSource
