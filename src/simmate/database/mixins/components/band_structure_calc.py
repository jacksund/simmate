# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..band_structure import BandStructureCalc


class BandStructureCalcComponent(TableComponent):
    table = BandStructureCalc
    display_name = "Band Structures"
