# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from .models import EnamineRealMolecule


class EnamineRealMoleculeTable(DynamicTableForm):
    table = EnamineRealMolecule
    html_display_name = "Enamine REAL"
    html_description_short = (
        "The Enamine REAL (REadily Accessible) database contains billions of "
        "accessible compounds that can be synthesized quickly using established "
        "chemical reactions. It is a premier resource for large-scale "
        "virtual screening."
    )
