# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import EppoCode


class EppoCodeTable(DynamicTableForm):
    table = EppoCode
    display_name = "EPPO Global Database"
    description_short = (
        "A standardized coding system for organisms, including plants, pests, "
        "and pathogens, maintained by the European and Mediterranean Plant "
        "Protection Organization (EPPO). These codes ensure unambiguous "
        "identification in agricultural and biological research."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "eppo_gd/eppo_codes/table.html",
    }
