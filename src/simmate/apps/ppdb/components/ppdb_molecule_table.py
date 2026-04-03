# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm, MoleculeInput

from ..models import PpdbMolecule


class PpdbMoleculeTable(DynamicTableForm, MoleculeInput):
    table = PpdbMolecule
    display_name = "PPDB"
    description_short = (
        "The Pesticide Properties DataBase (PPDB) provides comprehensive "
        "information on the physical, chemical, and environmental properties "
        "of pesticides, including toxicity and regulatory status."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "search": "core/base_data_types/molecule_form.html",
        "entries": "ppdb/molecules/table.html",
        "entry": "ppdb/molecules/view.html",
    }

    enabled_forms = ["search"]
