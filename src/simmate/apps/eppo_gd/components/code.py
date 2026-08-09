# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import EppoCode


class EppoCodeComponent(TableComponent):
    table = EppoCode
    display_name = "EPPO Global Database"
    description_short = (
        "A standardized coding system for organisms, including plants, pests, "
        "and pathogens, maintained by the European and Mediterranean Plant "
        "Protection Organization (EPPO). These codes ensure unambiguous "
        "identification in agricultural and biological research."
    )
    template_names = {
        "entries": "eppo_gd/eppo_codes/table.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry"]
