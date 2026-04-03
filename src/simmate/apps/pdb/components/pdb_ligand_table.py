# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm, MoleculeInput

from ..models import PdbLigand


class PdbLigandTable(DynamicTableForm, MoleculeInput):
    table = PdbLigand
    display_name = "PDB Ligands"
    description_short = (
        "Small molecules, ions, and ligands found within the structures of the "
        "Protein Data Bank (PDB). This dataset provides insights into how small "
        "molecules interact with biological macromolecules like proteins and DNA."
    )

    template_names = {
        "default": "pdb/ligand/form.html",
        "entry": "pdb/ligand/view.html",
        "entries": "pdb/ligand/table.html",
    }

    enabled_forms = ["search"]

    ignore_on_search = [
        *MoleculeInput.ignore_on_search,
    ]
