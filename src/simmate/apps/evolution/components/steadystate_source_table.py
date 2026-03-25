# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import SteadystateSource


class SteadystateSourceTable(DynamicTableForm):
    table = SteadystateSource
