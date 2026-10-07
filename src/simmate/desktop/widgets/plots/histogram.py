from collections.abc import Callable

import polars

from simmate.desktop.widgets.plots.bars import AGGREGATES, STACKING, HistogramPlot
from simmate.desktop.widgets.plots.base import PlotPanel
from simmate.desktop.widgets.plots.columns import DATE, NUMBER


class HistogramPanel(PlotPanel):
    """A histogram of one column, with bins to hover and click (see `GroupedBars`).

    Bars count their compounds by default, or aggregate another column (e.g. the mean
    pIC50 per MolWt bin), and counts can show as percents and/or add up (cumulative).
    """

    display_name = "Histogram"
    title = "Histogram"
    description = "How one column's values are spread out, in bins"

    def __init__(
        self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None = None
    ):
        super().__init__(df, svg_of)
        self.column_setting("column", "Column", (NUMBER, DATE), default="MolWt")
        self.choice_setting("bins", "Bins", ["10", "20", "30", "50", "100"], "20")
        self.choice_setting("aggregate", "Bar height", AGGREGATES, "Count")
        self.column_setting("of", "Of", (NUMBER,), optional=True)
        self.check_setting(
            "percent",
            "Show as percent of total",
            default=False,
            tooltip="Show each bar's count (or sum) as a percent of every bar's",
        )
        self.check_setting(
            "cumulative",
            "Cumulative",
            default=False,
            tooltip="Add up the bars from left to right",
        )
        self.check_setting(
            "show_filtered",
            "Show filtered-out compounds in grey",
            tooltip="Count compounds excluded by the filters in grey bars behind the "
            "others,\ninstead of leaving them out",
            on_change=self._redraw,
        )
        self.check_setting(
            "bin_hover",
            "Highlight a bin's compounds on hover",
            tooltip="While hovering a bar, highlight its compounds' rows and ring\n"
            "their points in the scatter plots",
            on_change=lambda: None,
        )

        self.histogram = HistogramPlot()
        self.histogram.bin_hovered.connect(self._on_bin_hover)
        self.histogram.bin_clicked.connect(
            lambda bin, modifiers: self.rows_clicked.emit(
                set(self.histogram.rows_in_bin(bin)), modifiers, None
            )
        )
        self.histogram.background_clicked.connect(self.background_clicked)
        self._build(self.histogram)
        self.draw()

    def check_inputs(self) -> str | None:
        if self.value("aggregate") != "Count" and not self.value("of"):
            return f"Choose a column in “Of” to take the {self.value('aggregate').lower()} of"
        return super().check_inputs()

    def _update_settings(self):
        aggregate = self.value("aggregate")
        self.settings["of"].setEnabled(aggregate != "Count")
        self.settings["percent"].setEnabled(aggregate in STACKING)
        self.settings["cumulative"].setEnabled(aggregate in STACKING)

    def _draw(self):
        """Re-bin after the column, bins or bar heights changed."""
        key, aggregate = self.value("column"), self.value("aggregate")

        self.histogram.set_values(self.columns.numbers(key), int(self.value("bins")))
        of = self.value("of")
        self.histogram.set_aggregate(
            aggregate,
            self.columns.numbers(of) if of and aggregate != "Count" else None,
            percent=self.value("percent"),
            cumulative=self.value("cumulative"),
        )
        self.set_axis("bottom", key)
        self.histogram.setLabel("left", self._height_label())
        self.histogram.set_selected(self.selected_rows)
        self._redraw()
        self.view_box.autoRange()  # emits view_changed via sigRangeChanged

    def _height_label(self) -> str:
        aggregate = self.value("aggregate")
        label = (
            "Count" if aggregate == "Count" else f"{aggregate} of {self.value('of')}"
        )
        if self.histogram.percent:
            label = f"Percent ({label.lower()})"
        if self.histogram.cumulative:
            label += ", cumulative"
        return label

    def _redraw(self):
        self.histogram.set_passing(self.passing, self.value("show_filtered"))

    def set_selected(self, rows: set[int]):
        super().set_selected(rows)
        if self._drawable():
            self.histogram.set_selected(rows)

    def show_hovered(self, rows: set[int]):
        # outline the bin of a single hovered compound
        if self._drawable():
            self.histogram.set_focus_bin(
                self.histogram.bin_of(next(iter(rows))) if len(rows) == 1 else None
            )

    def view_ranges(self) -> list[tuple[str, object, object]]:
        if not self._drawable():
            return []
        (low, high), _ = self.view_box.viewRange()
        return [self.columns.view_range(self.value("column"), low, high)]

    def _on_bin_hover(self, bin: int | None):
        self.histogram.set_focus_bin(bin)
        if bin is None:
            self.rows_hovered.emit(set())
            return
        rows = set(self.histogram.rows_in_bin(bin))
        if self.value("bin_hover"):
            self.rows_hovered.emit(rows)
        key = self.value("column")
        low, high = self.histogram.bin_range(bin)
        if self.histogram.cumulative:
            low = self.histogram.edges[0]
        text = (
            f"{key} {self.columns.format(key, low)} to "
            f"{self.columns.format(key, high)}: {len(rows)} compound(s)"
        )
        if self.value("aggregate") != "Count" or self.histogram.percent:
            text += f", {self._height_label().lower()} {self.histogram.passing_heights[bin]:.4g}"
        self.status.emit(text)
