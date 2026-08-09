# -*- coding: utf-8 -*-

from .ai_chatbot import AiChatbotFigure
from .bar import Bar
from .histogram import Histogram
from .line import Line
from .pie import Pie
from .scatter import Scatter
from .scatter_matrix import ScatterMatrix

ENABLED_CONSTRUCTORS = [
    AiChatbotFigure,
    Bar,
    Histogram,
    Line,
    Pie,
    Scatter,
    ScatterMatrix,
]


def get_plot_constructor_options():
    return [c.display_name for c in ENABLED_CONSTRUCTORS]
    # [
    #     "Describe to AI Chatbot",
    #     "Area",
    #     "Bar",
    #     "Bar",
    #     "Bar Polar",
    #     "Box",
    #     "Choropleth",
    #     "Choropleth Map",
    #     "Color Matrix (imshow)",
    #     "Density Contour",
    #     "Density Heatmap",
    #     "Density Map",
    #     "Ecdf",
    #     "Funnel",
    #     "Funnel Area",
    #     "Histogram",
    #     "Icicle",
    #     "Line 3D",
    #     "Line Geo",
    #     "Line Map",
    #     "Line Polar",
    #     "Line Ternary",
    #     "Parallel Categories",
    #     "Parallel Coordinates",
    #     "Pie",
    #     "Scatter",
    #     "Scatter 3D",
    #     "Scatter Geo",
    #     "Scatter Map",
    #     "Scatter Matrix",
    #     "Scatter Polar",
    #     "Scatter Ternary",
    #     "Strip",
    #     "Sunburst",
    #     "Timeline",
    #     "Voilin",
    # ]


def get_plot_constructor(plot_type):

    for constructor in ENABLED_CONSTRUCTORS:
        if constructor.display_name == plot_type:
            return constructor

    # if no match is found, raise an error
    raise Exception("Unknown plot_type!")
