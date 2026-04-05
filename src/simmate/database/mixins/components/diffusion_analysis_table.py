# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..nudged_elastic_band import DiffusionAnalysis


class DiffusionAnalysisTable(DynamicTableForm):
    table = DiffusionAnalysis
    display_name = "Diffusion Analysis"
