# -*- coding: utf-8 -*-

from django.core.exceptions import FieldDoesNotExist

from simmate.database.mixins.structure import Structure
from simmate.website.htmx.components import HtmxComponent
from simmate.website.htmx.components.mixins import (
    MoleculeInput,
    PeriodicTableInput,
)


class QuickSearchComponent(
    HtmxComponent,
    MoleculeInput,
    PeriodicTableInput,
):
    template_name = "data_explorer/components/quick_search.html"

    # State variables
    active_panel: str = (
        "periodic_table"  # 'periodic_table', 'sketcher', 'examples', None
    )
    search_query: str = ""
    search_results: dict = None

    def run_search(self, **kwargs):
        self.active_panel = "search_results"
        query = self.form_data.get("search_query", "").strip()
        self.search_query = query

        if not query:
            self.search_results = None
            return

        is_chemical_system = "-" in query
        if is_chemical_system:
            query_parts = query.split("-")
            query_parts.sort()
            query = "-".join(query_parts)

        results = {}

        from simmate.website.data_explorer.views import _SAFE_COMPONENTS

        for name, component in _SAFE_COMPONENTS.items():
            table = component.table

            is_structure = issubclass(table, Structure)
            is_substance = table.__name__ == "Substance"

            if not (is_structure or is_substance):
                continue

            if is_substance:
                filter_kwargs = (
                    {"structure__chemical_system": query}
                    if is_chemical_system
                    else {"structure__formula_reduced": query}
                )
            else:
                filter_kwargs = (
                    {"chemical_system": query}
                    if is_chemical_system
                    else {"formula_reduced": query}
                )

            qs = table.objects.filter(**filter_kwargs)

            if not qs.exists():
                continue

            try:
                table._meta.get_field("energy_above_hull")
                qs = qs.order_by("energy_above_hull", "id")
            except FieldDoesNotExist:
                qs = qs.order_by("id")

            top_results = list(qs[:5])

            results[name] = {
                "display_name": component.display_name,
                "url_name": name,
                "total_count": qs.count(),
                "entries": top_results,
                "has_ehull": hasattr(table, "energy_above_hull"),
                "url_query": query,
            }

        self.search_results = results

    def toggle_panel(self, **kwargs):
        """Toggles the active input helper panel."""
        panel = self.post_data.get("panel")
        if self.active_panel == panel:
            self.active_panel = None
        else:
            self.active_panel = panel

    def set_example(self, **kwargs):
        """Sets the search query to a predefined example."""
        self.search_query = self.post_data.get("query", "")
        self.active_panel = None

    def on_change_hook__search_query(self):
        """Preserves the user's input across panel toggles."""
        self.search_query = self.form_data.get("search_query") or ""

    def on_change_hook__molecule__molecule_sketcher(self):
        self.load_molecule("molecule")
        mol = self.form_data.get("molecule")
        if mol:
            self.search_query = mol.to_smiles()
