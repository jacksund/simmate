# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import MoleculeInput

from ..models import PdbLigand


class PdbLigandComponent(TableComponent, MoleculeInput):
    table = PdbLigand
    display_name = "PDB Ligands"
    description_short = (
        "Small molecules, ions, and ligands found within the structures of the "
        "Protein Data Bank (PDB). This dataset provides insights into how small "
        "molecules interact with biological macromolecules like proteins and DNA."
    )

    template_names = {
        "search": "pdb/ligand/form.html",
        "entry": "pdb/ligand/view.html",
        "entries": "pdb/ligand/table.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]

    ignore_on_search = [
        *MoleculeInput.ignore_on_search,
    ]
