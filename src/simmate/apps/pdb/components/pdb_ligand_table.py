# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import PdbLigand


class PdbLigandTable(DynamicTableForm):
    table = PdbLigand
    display_name = "PDB Ligands"
    description_short = (
        "Small molecules, ions, and ligands found within the structures of the "
        "Protein Data Bank (PDB). This dataset provides insights into how small "
        "molecules interact with biological macromolecules like proteins and DNA."
    )
