# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import OqmdStructure


class OqmdStructureTable(DynamicTableForm):
    table = OqmdStructure
    display_name = "OQMD"
    description_short = (
        "The Open Quantum Materials Database (OQMD) provides high-throughput "
        "calculations of thermodynamic and structural properties for a "
        "comprehensive set of inorganic materials, with a focus on formation "
        "energies and convex hull analysis."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "oqmd/structures/table.html",
        "entry": "oqmd/structures/view.html",
    }
