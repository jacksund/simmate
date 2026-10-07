from collections.abc import Callable

import numpy as np
import polars

from simmate.desktop.widgets.plots.bars import AGGREGATES, STACKING, GroupedBars
from simmate.desktop.widgets.plots.base import PlotPanel
from simmate.desktop.widgets.plots.columns import CATEGORY, NUMBER

BAR_WIDTH = 0.8  # of each category's slot


class BarPanel(PlotPanel):
    """A bar per category (e.g. per series), counting its compounds or aggregating a
    column over them. Bars hover and click like a histogram's bins.

    The axis is categorical, so zooming it doesn't narrow the table.
    """

    display_name = "Bar"
    title = "Bar chart"
    description = "A bar per category, counting its compounds or averaging a column"

    def __init__(
        self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None = None
    ):
        super().__init__(df, svg_of)
        self.column_setting("category", "Category", (CATEGORY,), default="series")
        self.choice_setting("aggregate", "Bar height", AGGREGATES, "Count")
        self.column_setting("of", "Of", (NUMBER,), optional=True)
        self.check_setting(
            "percent",
            "Show as percent of total",
            default=False,
            tooltip="Show each bar's count (or sum) as a percent of every bar's",
        )
        self.choice_setting("sort", "Order", ["By name", "Tallest first"])
        self.check_setting(
            "show_filtered",
            "Show filtered-out compounds in grey",
            tooltip="Count compounds excluded by the filters in grey bars behind the "
            "others,\ninstead of leaving them out",
            on_change=self._redraw,
        )
        self.check_setting(
            "bar_hover",
            "Highlight a bar's compounds on hover",
            tooltip="While hovering a bar, highlight its compounds' rows and ring\n"
            "their points in the scatter plots",
            on_change=lambda: None,
        )

        self.bars = GroupedBars()
        self.bars.showGrid(x=False, y=True, alpha=0.3)  # no lines between categories
        self.bars.bin_hovered.connect(self._on_bar_hover)
        self.bars.bin_clicked.connect(
            lambda bar, modifiers: self.rows_clicked.emit(
                set(self.bars.rows_in_bin(bar)), modifiers, None
            )
        )
        self.bars.background_clicked.connect(self.background_clicked)
        self._build(self.bars)
        self.draw()

    def check_inputs(self) -> str | None:
        if self.value("aggregate") != "Count" and not self.value("of"):
            return f"Choose a column in “Of” to take the {self.value('aggregate').lower()} of"
        return super().check_inputs()

    def _update_settings(self):
        aggregate = self.value("aggregate")
        self.settings["of"].setEnabled(aggregate != "Count")
        self.settings["percent"].setEnabled(aggregate in STACKING)

    def _draw(self):
        key, aggregate = self.value("category"), self.value("aggregate")
        codes, self.labels = self.columns.codes(key)
        of = self.value("of")
        self.bars.set_aggregate(
            aggregate,
            self.columns.numbers(of) if of and aggregate != "Count" else None,
            percent=self.value("percent"),
        )

        # Order the bars once, by every row, so they don't shuffle as filters change.
        positions = np.arange(len(self.labels), dtype=float)
        self.bars.set_groups(codes, positions, positions + 1)
        if self.value("sort") == "Tallest first":
            heights, _ = self.bars._aggregated(np.ones(len(codes), dtype=bool))
            positions[np.argsort(-heights, kind="stable")] = np.arange(len(self.labels))
        self.bars.set_groups(
            codes, positions - BAR_WIDTH / 2, positions + BAR_WIDTH / 2
        )

        self.set_axis("bottom", key)
        self.bars.getAxis("bottom").setTicks(
            [list(zip(positions.tolist(), self.labels))]
        )
        label = "Count" if aggregate == "Count" else f"{aggregate} of {of}"
        if self.bars.percent:
            label = f"Percent ({label.lower()})"
        self.height_label = label
        self.bars.setLabel("left", label)
        self.bars.set_selected(self.selected_rows)
        self._redraw()
        self.view_box.autoRange()

    def _redraw(self):
        self.bars.set_passing(self.passing, self.value("show_filtered"))

    def set_selected(self, rows: set[int]):
        super().set_selected(rows)
        if self._drawable():
            self.bars.set_selected(rows)

    def show_hovered(self, rows: set[int]):
        # outline the bar of a single hovered compound
        if self._drawable():
            self.bars.set_focus_bin(
                self.bars.bin_of(next(iter(rows))) if len(rows) == 1 else None
            )

    def _on_bar_hover(self, bar: int | None):
        self.bars.set_focus_bin(bar)
        if bar is None:
            self.rows_hovered.emit(set())
            return
        rows = set(self.bars.rows_in_bin(bar))
        if self.value("bar_hover"):
            self.rows_hovered.emit(rows)
        text = f"{self.value('category')} {self.labels[bar]}: {len(rows)} compound(s)"
        if self.value("aggregate") != "Count" or self.bars.percent:
            text += (
                f", {self.height_label.lower()} {self.bars.passing_heights[bar]:.4g}"
            )
        self.status.emit(text)
