# -*- coding: utf-8 -*-

# The order that we import these different modules is important to prevent
# circular imports errors, so we prevent isort from changing this file.
# isort: skip_file

from .figure import Figure

from .matplotlib import MatplotlibFigure
from .plotly import PlotlyFigure
