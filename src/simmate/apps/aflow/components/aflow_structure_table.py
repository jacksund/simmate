# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import AflowPrototype, AflowStructure


class AflowStructureTable(DynamicTableForm):
    table = AflowStructure
    display_name = "AFLOW"
    description_short = (
        "A database of computed and experimental crystal structures from the "
        "Automatic-FLOW for Materials Discovery (AFLOW) repository. It includes "
        "a vast collection of alloy and inorganic compounds with "
        "high-throughput characterization."
    )
