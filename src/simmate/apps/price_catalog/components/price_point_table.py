# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import PricePoint


class PricePointTable(DynamicTableForm):
    table = PricePoint
