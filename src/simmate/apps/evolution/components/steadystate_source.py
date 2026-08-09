# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import SteadystateSource


class SteadystateSourceComponent(TableComponent):
    table = SteadystateSource
