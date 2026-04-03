# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm, MoleculeInput

from ..models import CasRegistryMolecule


class CasRegistryMoleculeTable(DynamicTableForm, MoleculeInput):
    table = CasRegistryMolecule
    display_name = "CAS Registry"
    description_short = (
        "A collection of chemical substances identified by CAS Registry Numbers. "
        "It provides a unique and universally recognized identity for millions "
        "of elements, compounds, and polymers, serving as the gold standard "
        "for chemical identification."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "search": "core/base_data_types/molecule_form.html",
    }

    enabled_forms = ["search"]
