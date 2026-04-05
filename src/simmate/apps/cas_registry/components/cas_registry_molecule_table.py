# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm
from simmate.website.htmx.components import MoleculeInput

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
        "default": "cas_registry/molecule/form.html",
        "entry": "cas_registry/molecule/view.html",
        "entries": "cas_registry/molecule/table.html",
    }

    enabled_forms = ["search"]

    ignore_on_search = [
        *MoleculeInput.ignore_on_search,
    ]
