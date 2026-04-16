# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import AflowPrototype


class AflowPrototypeComponent(TableComponent):
    table = AflowPrototype
    display_name = "AFLOW Prototypes"
    description_short = (
        "A library of crystal structure templates (prototypes) from the AFLOW "
        "Encyclopedia of Crystallographic Prototypes. These templates allow "
        "researchers to rapidly generate new candidate materials by substituting "
        "different elements into known symmetry sites."
    )
    template_names = {
        "entries": "aflow/prototype/table.html",
        "entry": "aflow/prototype/view.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry"]
