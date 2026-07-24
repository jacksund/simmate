# -*- coding: utf-8 -*-

from simmate.website.htmx.components import HtmxComponent
from simmate.website.htmx.components.mixins import (
    MoleculeInput,
    PeriodicTableInput,
    StructureInput,
)


class QuickSearchComponent(
    HtmxComponent,
    MoleculeInput,
    StructureInput,
    PeriodicTableInput,
):
    template_name = "data_explorer/components/quick_search.html"

    # State variables
    active_panel: str = (
        "periodic_table"  # 'periodic_table', 'sketcher', 'upload', 'examples', None
    )
    search_query: str = ""

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
        self.search_query = self.form_data.get("search_query", "")

    def on_change_hook__molecule__molecule_sketcher(self):
        self.load_molecule("molecule")
        mol = self.form_data.get("molecule")
        if mol:
            self.search_query = mol.to_smiles()

    def on_change_hook__structure__file(self):
        self.load_structure("structure")
        struct = self.form_data.get("structure")
        if struct:
            self.search_query = struct.composition.reduced_formula
