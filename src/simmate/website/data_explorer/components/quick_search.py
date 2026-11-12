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

    substances_only: bool = False
    """
    Whether to only search the `Substance` table (e.g. for the inventory
    dashboard).
    """

    substance_filters = {
        "id": "id",
        "name": "common_name__icontains",
        "chemical_system": "structure__chemical_system",
        "formula_reduced": "structure__formula_reduced",
        "inchi_key": "molecule__inchi_key",
    }
    """
    The `Substance` table filter to use for each type of query (see
    `parse_query`).
    """

    @staticmethod
    def parse_query(query: str, substance_table=None) -> tuple[str, str]:
        """
        Figures out what kind of search query this is, which sets the column
        to search on (and the normalized value to search for).

        Formulas only match if they are already written as a reduced formula
        (e.g. "Fe2O3"), since that is how they are stored. This also lets
        SMILES that happen to be valid formulas (e.g. "CCO") fall through to a
        molecule search. Short queries that are both (e.g. "CO") are treated as
        formulas. Anything else is treated as a name (e.g. "DMSO").

        Args:
            query: The text that the user searched for.
            substance_table: The `Substance` table, which is used to check for
                substance IDs. IDs are not checked when this is not given
                (e.g. when the inventory app is not installed).

        Returns:
            The query type (one of "id", "chemical_system", "formula_reduced",
            "inchi_key", or "name") and the value to search for. For SMILES,
            the value is converted to an InChIKey.
        """
        if substance_table and substance_table.validate_id(query):
            return "id", query
        if re.fullmatch(r"[A-Z][a-z]?(-[A-Z][a-z]?)+", query):
            return "chemical_system", "-".join(sorted(query.split("-")))
        try:
            is_formula = Composition(query).reduced_formula == query
        except Exception:
            is_formula = False
        if is_formula:
            return "formula_reduced", query
        try:
            return "inchi_key", ToolkitMolecule.from_smiles(query).to_inchi_key()
        except Exception:
            return "name", query

    def run_search(self, **kwargs):
        self.active_panel = "search_results"
        query = self.form_data.get("search_query", "").strip()
        self.search_query = query

        if not query:
            self.search_results = None
            return

        from simmate.website.data_explorer.views import _SAFE_COMPONENTS

        # The substance table is found through the searchable components
        # (rather than imported) because its app is optional
        substance_component = _SAFE_COMPONENTS.get("Substance")

        search_field, query = self.parse_query(
            query,
            substance_table=substance_component.table if substance_component else None,
        )

        results = {}

        for name, component in _SAFE_COMPONENTS.items():
            table = component.table

            is_structure = issubclass(table, Structure)
            is_substance = component is substance_component

            if self.substances_only and not is_substance:
                continue

            # Substances are searched via their ID, name, or linked molecule
            # or crystal structure, depending on the query type
            if is_substance:
                url_filter = self.substance_filters[search_field]
                if search_field == "id":
                    # follows merged IDs and loads datastore-only substances
                    try:
                        query = table.get_by_id(query).id
                    except table.DoesNotExist:
                        continue
            elif is_structure and search_field in (
                "chemical_system",
                "formula_reduced",
            ):
                url_filter = search_field
            else:
                continue

            qs = table.objects.filter(**{url_filter: query})
            if is_substance:
                qs = qs.select_related("molecule", "structure")

            try:
                table._meta.get_field("energy_above_hull")
                qs = qs.order_by("energy_above_hull", "id")
            except FieldDoesNotExist:
                qs = qs.order_by("id")

            top_results = list(qs[:5])
            if not top_results:
                continue

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
