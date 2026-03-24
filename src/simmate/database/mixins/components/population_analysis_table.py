# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..population_analysis import PopulationAnalysis


class PopulationAnalysisTable(DynamicTableForm):
    table = PopulationAnalysis
    display_name = "Population Analysis"
