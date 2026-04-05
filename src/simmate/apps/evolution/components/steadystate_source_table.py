# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import SteadystateSource


class SteadystateSourceTable(DynamicTableForm):
    table = SteadystateSource
