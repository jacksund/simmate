# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import Bader


class BaderComponent(TableComponent):
    table = Bader
    display_name = "BaderKit Charge Analysis"
    description_short = "Results for BaderKit Charge Analysis Calculations"
