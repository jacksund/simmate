# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..nudged_elastic_band import DiffusionAnalysis


class DiffusionAnalysisComponent(TableComponent):
    table = DiffusionAnalysis
    display_name = "Diffusion Analysis"
