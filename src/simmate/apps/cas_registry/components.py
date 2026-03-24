# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from .models import CasRegistryMolecule


class CasRegistryMoleculeTable(DynamicTableForm):
    table = CasRegistryMolecule
    html_display_name = "CAS Registry"
    html_description_short = (
        "A collection of chemical substances identified by CAS Registry Numbers. "
        "It provides a unique and universally recognized identity for millions "
        "of elements, compounds, and polymers, serving as the gold standard "
        "for chemical identification."
    )
