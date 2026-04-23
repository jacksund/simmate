# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..population_analysis import PopulationAnalysis


class PopulationAnalysisComponent(TableComponent):
    table = PopulationAnalysis
    display_name = "Population Analysis"
