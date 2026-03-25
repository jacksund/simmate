# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import ChemblAssayResult, ChemblDocument, ChemblMolecule


class ChemblMoleculeTable(DynamicTableForm):
    table = ChemblMolecule
    display_name = "ChEMBL"
    description_short = (
        "A manually curated database of bioactive molecules from ChEMBL, "
        "providing drug-like properties and structure-activity relationships. "
        "It includes data on chemical structures, biological assays, and "
        "target interactions, making it a key resource for drug discovery."
    )
