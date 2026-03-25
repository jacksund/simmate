# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..nudged_elastic_band import DiffusionAnalysis


class DiffusionAnalysisTable(DynamicTableForm):
    table = DiffusionAnalysis
    display_name = "Diffusion Analysis"
