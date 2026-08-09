# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import StructureInput

from ..models import AflowStructure


class AflowStructureComponent(TableComponent, StructureInput):
    table = AflowStructure
    display_name = "AFLOW"
    description_short = (
        "A database of computed and experimental crystal structures from the "
        "Automatic-FLOW for Materials Discovery (AFLOW) repository. It includes "
        "a vast collection of alloy and inorganic compounds with "
        "high-throughput characterization."
    )
    template_names = {
        "search": "aflow/structures/form.html",
        "entries": "aflow/structures/table.html",
        "entry": "aflow/structures/view.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]
