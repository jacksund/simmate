# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm, StructureInput

from ..models import JarvisStructure


class JarvisStructureTable(DynamicTableForm, StructureInput):
    table = JarvisStructure
    display_name = "JARVIS"
    description_short = (
        "A collection of materials data for high-throughput discovery from "
        "NIST's JARVIS project. This dataset focuses on 2D and 3D materials "
        "with high-fidelity calculations of electronic, optical, and "
        "mechanical properties."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "search": "jarvis/structures/form.html",
        "entries": "jarvis/structures/table.html",
        "entry": "jarvis/structures/view.html",
    }

    enabled_forms = ["search"]
