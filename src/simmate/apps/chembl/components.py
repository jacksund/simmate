# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from .models import ChemblMolecule, ChemblAssayResult, ChemblDocument


class ChemblMoleculeTable(DynamicTableForm):
    table = ChemblMolecule
    html_display_name = "ChEMBL"
    html_description_short = (
        "A manually curated database of bioactive molecules from ChEMBL, "
        "providing drug-like properties and structure-activity relationships. "
        "It includes data on chemical structures, biological assays, and "
        "target interactions, making it a key resource for drug discovery."
    )


class ChemblAssayResultTable(DynamicTableForm):
    table = ChemblAssayResult


class ChemblDocumentTable(DynamicTableForm):
    table = ChemblDocument
