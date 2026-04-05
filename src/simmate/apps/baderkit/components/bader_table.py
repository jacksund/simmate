# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import Bader


class BaderTable(DynamicTableForm):
    table = Bader
    display_name = "BaderKit Charge Analysis"
    description_short = "Results for BaderKit Charge Analysis Calculations"
