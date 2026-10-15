# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import MoleculeInput

from ..models import ChemblDocument, ChemblMolecule


class ChemblMoleculeComponent(TableComponent, MoleculeInput):
    """
    A dynamic table and search form for ChEMBL molecules.
    """

    table = ChemblMolecule
    display_name = "ChEMBL"
    description_short = (
        "A manually curated database of bioactive molecules from ChEMBL, "
        "providing drug-like properties and structure-activity relationships. "
        "It includes data on chemical structures, biological assays, and "
        "target interactions, making it a key resource for drug discovery."
    )

    template_names = {
        "search": "chembl/molecule/form.html",
        "entry": "chembl/molecule/view.html",
        "entries": "chembl/molecule/table.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]

    ignore_on_search = [
        *MoleculeInput.ignore_on_search,
    ]

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: ChemblMolecule) -> dict:

        assays__limit = 100
        assays = table_entry.chembl_assay_results.order_by("id").all()
        assays__count = assays.count()

        documents = ChemblDocument.objects.filter(
            chembl_assay_results__chembl_compound=table_entry
        ).distinct()

        return {
            "assays": assays[:assays__limit],
            "assays__count": assays__count,
            "assays__truncated": assays__count > assays__limit,
            "documents": documents.order_by("-published_at", "id"),
            "documents__count": documents.count(),
        }
