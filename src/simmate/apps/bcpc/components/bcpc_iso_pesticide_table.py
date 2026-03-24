# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import BcpcIsoPesticide


class BcpcIsoPesticideTable(DynamicTableForm):
    table = BcpcIsoPesticide
    display_name = "ISO Pesticides"
    description_short = (
        "A standardized set of pesticide active ingredients as defined by the "
        "British Crop Production Council (BCPC). This compendium provides common "
        "names, chemical identities, and classification for essential "
        "agrochemicals."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "bcpc/iso_pesticides/table.html",
        "entry": "bcpc/iso_pesticides/view.html",
    }
