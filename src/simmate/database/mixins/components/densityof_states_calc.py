# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..density_of_states import DensityofStatesCalc


class DensityofStatesCalcComponent(TableComponent):
    table = DensityofStatesCalc
    display_name = "Density of States"
