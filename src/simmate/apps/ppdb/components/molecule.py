# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import MoleculeInput

from ..models import PpdbMolecule


class PpdbMoleculeComponent(TableComponent, MoleculeInput):
    table = PpdbMolecule
    display_name = "PPDB"
    description_short = (
        "The Pesticide Properties DataBase (PPDB) provides comprehensive "
        "information on the physical, chemical, and environmental properties "
        "of pesticides, including toxicity and regulatory status."
    )
    template_names = {
        "search": "core/base_data_types/molecule_form.html",
        "entries": "ppdb/molecules/table.html",
        "entry": "ppdb/molecules/view.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]
