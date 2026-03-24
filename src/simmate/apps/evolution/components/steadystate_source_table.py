# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import (
    ChemicalSystemSearch,
    FixedCompositionSearch,
    SteadystateSource,
    VariableNsitesCompositionSearch,
)


class SteadystateSourceTable(DynamicTableForm):
    table = SteadystateSource
