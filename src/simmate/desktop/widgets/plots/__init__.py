# -*- coding: utf-8 -*-

"""The plots that can be added to the Toolkit tab, one module per type.

Every type subclasses `PlotPanel` (see `base.py`) and is drawn with pyqtgraph's
native items, so plots stay fast and keep the dashboard's linked hover, selection
and zoom-to-filter. To add a type, write a `PlotPanel` subclass and list it below.

Roadmap: plot types with no native pyqtgraph item, for later. Each would still be a
`PlotPanel` subclass, so the dashboard and layout wouldn't change.

- With matplotlib (`FigureCanvasQTAgg`; installed via pymatgen, but not listed in
  pyproject.toml): box, strip, violin, pie, density heatmap/contour, parallel
  coordinates, polar. Static images, so linking would be basic: redraw on filter
  and selection changes, with `mpl_connect` pick events for clicks.
- With plotly (`QWebEngineView`, as the Ketcher sketcher uses; plotly is already a
  dependency): the rest of plotly express, e.g. sunburst, icicle, treemap, funnel,
  parallel categories, ternary, timeline, 3D scatter/line, and geo/map/choropleth.
  Linking needs a JS <-> Python bridge (`QWebChannel`) for hover, selection and
  relayout (zoom) events; heavier per pane, and slow past ~10k points.
- As pyqtgraph composites, keeping full linking: box/strip (bars and lines from our
  own statistics), scatter matrix (linked `PlotItem`s in a `GraphicsLayoutWidget`),
  density heatmap (`ImageItem`).

See `simmate/apps/analysis_dashboard/plot_constructors/` for the older plotly
versions of many of these.
"""

from .ai import AiPlotPanel
from .bar import BarPanel
from .bars import GroupedBars, HistogramPlot
from .base import PlotPanel
from .chooser import PlotTypeChooser
from .columns import DataColumns
from .histogram import HistogramPanel
from .line import LinePanel
from .scatter import ScatterPanel

# The plots that can be added to the dashboard, by the name shown for each.
PLOT_TYPES: dict[str, type[PlotPanel]] = {
    cls.display_name: cls
    for cls in [ScatterPanel, HistogramPanel, BarPanel, LinePanel, AiPlotPanel]
}
