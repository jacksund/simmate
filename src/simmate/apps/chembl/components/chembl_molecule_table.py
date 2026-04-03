# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm, MoleculeInput

from ..models import ChemblMolecule


class ChemblMoleculeTable(DynamicTableForm, MoleculeInput):
    table = ChemblMolecule
    display_name = "ChEMBL"
    description_short = (
        "A manually curated database of bioactive molecules from ChEMBL, "
        "providing drug-like properties and structure-activity relationships. "
        "It includes data on chemical structures, biological assays, and "
        "target interactions, making it a key resource for drug discovery."
    )

    template_names = {
        "default": "chembl/molecule/form.html",
        "entry": "chembl/molecule/view.html",
        "entries": "chembl/molecule/table.html",
    }

    enabled_forms = ["search"]

    ignore_on_search = [
        *MoleculeInput.ignore_on_search,
    ]
