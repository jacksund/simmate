# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..density_of_states import DensityofStatesCalc


class DensityofStatesCalcTable(DynamicTableForm):
    table = DensityofStatesCalc
    display_name = "Density of States"
