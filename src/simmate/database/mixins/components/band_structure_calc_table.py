# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..band_structure import BandStructureCalc


class BandStructureCalcTable(DynamicTableForm):
    table = BandStructureCalc
    display_name = "Band Structures"
