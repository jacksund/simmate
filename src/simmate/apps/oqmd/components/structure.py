# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import StructureInput

from ..models import OqmdStructure


class OqmdStructureComponent(TableComponent, StructureInput):
    table = OqmdStructure
    display_name = "OQMD"
    description_short = (
        "The Open Quantum Materials Database (OQMD) provides high-throughput "
        "calculations of thermodynamic and structural properties for a "
        "comprehensive set of inorganic materials, with a focus on formation "
        "energies and convex hull analysis."
    )
    template_names = {
        "search": "oqmd/structures/form.html",
        "entries": "oqmd/structures/table.html",
        "entry": "oqmd/structures/view.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]
