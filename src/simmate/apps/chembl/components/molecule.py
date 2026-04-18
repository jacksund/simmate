# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import MoleculeInput

from ..models import ChemblMolecule


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
