# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import MoleculeInput

from ..models import CasRegistryMolecule


class CasRegistryMoleculeComponent(TableComponent, MoleculeInput):
    table = CasRegistryMolecule
    display_name = "CAS Registry"
    description_short = (
        "A collection of chemical substances identified by CAS Registry Numbers. "
        "It provides a unique and universally recognized identity for millions "
        "of elements, compounds, and polymers, serving as the gold standard "
        "for chemical identification."
    )
    template_names = {
        "search": "cas_registry/molecule/form.html",
        "entry": "cas_registry/molecule/view.html",
        "entries": "cas_registry/molecule/table.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]

    ignore_on_search = [
        *MoleculeInput.ignore_on_search,
    ]
