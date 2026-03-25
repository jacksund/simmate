# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..density_of_states import DensityofStatesCalc


class DensityofStatesCalcTable(DynamicTableForm):
    table = DensityofStatesCalc
    display_name = "Density of States"
