import re

from django.core.exceptions import FieldDoesNotExist

from simmate.database.mixins.structure import Structure
from simmate.toolkit import Composition
from simmate.toolkit import Molecule as ToolkitMolecule
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

        # Figure out what kind of query this is, which sets the column we
        # search on (and the normalized value to search for). Formulas only
        # match if they are already written as a reduced formula (e.g. "Fe2O3"),
        # since that is how they are stored. This also lets SMILES that happen
        # to be valid formulas (e.g. "CCO") fall through to a molecule search.
        # Short queries that are both (e.g. "CO") are treated as formulas.
        if re.fullmatch(r"[A-Z][a-z]?(-[A-Z][a-z]?)+", query):
            search_field = "chemical_system"
            query = "-".join(sorted(query.split("-")))
        else:
            try:
                is_formula = Composition(query).reduced_formula == query
            except Exception:
                is_formula = False
            try:
                inchi_key = ToolkitMolecule.from_smiles(query).to_inchi_key()
            except Exception:
                inchi_key = None
            if inchi_key and not is_formula:
                search_field = "inchi_key"
                query = inchi_key
            else:
                # if neither parses, we still try a formula search
                search_field = "formula_reduced"

        results = {}

        from simmate.website.data_explorer.views import _SAFE_COMPONENTS

        for name, component in _SAFE_COMPONENTS.items():
            table = component.table

            is_structure = issubclass(table, Structure)
            is_substance = table.__name__ == "Substance"

            # Substances are searched via their linked molecule or crystal
            # structure, depending on the query type
            if is_substance:
                url_filter = {
                    "chemical_system": "structure__chemical_system",
                    "formula_reduced": "structure__formula_reduced",
                    "inchi_key": "molecule__inchi_key",
                }[search_field]
            elif is_structure and search_field != "inchi_key":
                url_filter = search_field
            else:
                continue

            qs = table.objects.filter(**{url_filter: query})
            if is_substance:
                qs = qs.select_related("molecule", "structure")

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
                "is_substance": is_substance,
                "url_filter": url_filter,
                "url_query": query,
            }

        self.search_results = results

    def reset_search(self, **kwargs):
        """Clears the search query, results, and restores the default panel."""
        self.search_query = ""
        self.search_results = None
        self.active_panel = "periodic_table"

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
