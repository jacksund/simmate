# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import AflowPrototype, AflowStructure


class AflowPrototypeTable(DynamicTableForm):
    table = AflowPrototype
    display_name = "AFLOW Prototypes"
    description_short = (
        "A library of crystal structure templates (prototypes) from the AFLOW "
        "Encyclopedia of Crystallographic Prototypes. These templates allow "
        "researchers to rapidly generate new candidate materials by substituting "
        "different elements into known symmetry sites."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "aflow/prototype/table.html",
        "entry": "aflow/prototype/view.html",
    }
