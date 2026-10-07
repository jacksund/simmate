from collections.abc import Callable

import numpy as np
import polars
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.widgets.inputs import StyledCheckBox, StyledComboBox, input_style
from simmate.desktop.widgets.plot_toolbar import ResetViewButton, SettingsButton
from simmate.desktop.widgets.plots.columns import DATE, NUMBER, DataColumns

NONE = "None"  # the choice for an optional column left unset
OPACITIES = ["100%", "80%", "60%", "40%", "20%"]


class PlotPanel(QWidget):
    """One plot of the dashboard's rows, with its toolbar and settings above it.

    Each type of plot subclasses this (see `PLOT_TYPES`). Plots know nothing about
    each other or the table: they report what the user does through signals, and the
    dashboard tells every plot what to show through the `set_*`/`show_hovered` methods.

    - `rows_hovered(rows)`: the rows under the cursor changed (empty once off them).
    - `rows_clicked(rows, modifiers, row)`: rows were clicked; `row` is the one
      clicked on, if it was a single row (else None).
    - `background_clicked()`: a plain click on empty plot space.
    - `view_changed()`: the plot was zoomed or panned.
    - `status(text)`: a message for the status bar.

    A subclass declares its settings in `__init__` with the `*_setting` methods
    (each named, so `config`/`apply_config` can read and set them all as a dict),
    then calls `_build` with its plot. `draw` (re)draws everything after a setting
    changes, and `_redraw` the data after the filters change. `check_inputs` can
    report settings that can't be drawn, which then shows instead of the plot.
    """

    display_name = "Plot"  # in the plot type chooser
    title = "Plot"  # above the pane, while editing the layout
    description = ""  # the chooser's tooltip
    preview = False  # not working yet: marked in the chooser

    rows_hovered = Signal(object)
    rows_clicked = Signal(object, object, object)
    background_clicked = Signal()
    view_changed = Signal()
    status = Signal(str)

    def __init__(
        self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None = None
    ):
        super().__init__()
        self.df = df
        self.columns = DataColumns(df)
        # how a row's compound is drawn, e.g. for a card on hover
        self.svg_of = svg_of
        # By row index: which rows pass the filters.
        self.passing = np.ones(df.height, dtype=bool)
        self.selected_rows: set[int] = set()
        self.settings: dict[str, QWidget] = {}
        self._setting_rows: list = []  # (label, input) pairs, or an input alone
        self._required_columns: list[tuple[str, str]] = []  # (name, label)
        self._column_settings: set[str] = set()  # whose "None" means no column
        self.plot: pg.PlotWidget | None = None
        self.view_box: pg.ViewBox | None = None

    # --- settings -------------------------------------------------------------------------

    def column_setting(
        self,
        name: str,
        label: str,
        kinds: tuple[str, ...],
        default: str | None = None,
        fallback: int = 0,
        optional: bool = False,
        on_change: Callable | None = None,
    ) -> StyledComboBox:
        """A choice of the columns of `kinds`. It starts at `default` if there is
        such a column, else the `fallback`-th one (or "None" when `optional`)."""
        options = self.columns.of_kind(*kinds)
        combo = StyledComboBox()
        combo.addItems([NONE] + options if optional else options)
        if default in options:
            combo.setCurrentText(default)
        elif not optional and options:
            combo.setCurrentIndex(min(fallback, len(options) - 1))
        self._column_settings.add(name)
        if not optional:
            self._required_columns.append((name, label))
        return self._add_setting(name, label, combo, on_change)

    def choice_setting(
        self,
        name: str,
        label: str,
        options: list[str],
        default: str | None = None,
        on_change: Callable | None = None,
    ) -> StyledComboBox:
        combo = StyledComboBox()
        combo.addItems(options)
        if default:
            combo.setCurrentText(default)
        return self._add_setting(name, label, combo, on_change)

    def check_setting(
        self,
        name: str,
        label: str,
        default: bool = True,
        tooltip: str = "",
        on_change: Callable | None = None,
    ) -> StyledCheckBox:
        checkbox = StyledCheckBox(label)
        checkbox.setToolTip(tooltip)
        checkbox.setChecked(default)
        return self._add_setting(name, None, checkbox, on_change)

    def opacity_setting(self, on_change: Callable | None = None) -> StyledComboBox:
        return self.choice_setting("opacity", "Opacity", OPACITIES, on_change=on_change)

    def _add_setting(self, name, label, widget, on_change):
        self.settings[name] = widget
        self._setting_rows.append((label, widget) if label else widget)
        callback = on_change or self.draw
        if isinstance(widget, StyledCheckBox):
            widget.toggled.connect(lambda _: callback())
        else:
            widget.currentTextChanged.connect(lambda _: callback())
        return widget

    def value(self, name: str):
        """A setting's value: a checkbox's state, else the choice (None for a column
        left unset)."""
        widget = self.settings[name]
        if isinstance(widget, StyledCheckBox):
            return widget.isChecked()
        if name == "opacity":
            return int(widget.currentText().rstrip("%")) / 100
        text = widget.currentText()
        if name in self._column_settings and text in (NONE, ""):
            return None
        return text

    def config(self) -> dict:
        """Every setting by name, e.g. to save the plot or to set by `apply_config`."""
        return {
            name: (
                widget.isChecked()
                if isinstance(widget, StyledCheckBox)
                else widget.currentText()
            )
            for name, widget in self.settings.items()
        }

    def apply_config(self, config: dict):
        """Set the settings in `config` (as from `config`), then redraw once.
        Unknown names, and choices that aren't on offer, are skipped."""
        for name, value in config.items():
            widget = self.settings.get(name)
            if widget is None:
                continue
            widget.blockSignals(True)
            if isinstance(widget, StyledCheckBox):
                widget.setChecked(bool(value))
            elif widget.findText(str(value)) >= 0:
                widget.setCurrentText(str(value))
            widget.blockSignals(False)
        self.draw()

    def check_inputs(self) -> str | None:
        """Why the settings can't be drawn (shown in place of the plot), or None."""
        for name, label in self._required_columns:
            if self.settings[name].count() == 0:
                return f"There are no columns to use for “{label}”"
        return None

    # --- layout ---------------------------------------------------------------------------

    def _build(self, plot: pg.PlotWidget | None):
        """Lay out `plot` under its toolbar, with a settings panel of every declared
        setting. A plot of None (e.g. a placeholder) gets no toolbar buttons."""
        self.plot = plot
        settings_panel = QWidget()
        settings_panel.setStyleSheet(input_style())  # same inputs as the filters
        settings_layout = QFormLayout(settings_panel)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        settings_layout.setHorizontalSpacing(12)
        settings_layout.setVerticalSpacing(10)
        for row in self._setting_rows:
            if isinstance(row, tuple):
                settings_layout.addRow(*row)
            else:
                settings_layout.addRow(row)

        controls = QHBoxLayout()
        controls.setSpacing(2)  # the two buttons sit close together
        controls.addStretch()
        if plot is not None:
            self.view_box = plot.getPlotItem().getViewBox()
            self.view_box.sigRangeChanged.connect(lambda *_: self.view_changed.emit())
            controls.addWidget(ResetViewButton(plot))
        if self._setting_rows:
            controls.addWidget(
                SettingsButton(settings_panel, tooltip=f"{self.title} settings")
            )

        # why the plot can't be drawn, in its place
        self.message = QLabel()
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setWordWrap(True)
        self.message.setStyleSheet(f"color: {theme.MUTED_COLOR};")
        self.stack = QStackedWidget()
        if plot is not None:
            self.stack.addWidget(plot)
        self.stack.addWidget(self.message)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)  # between the buttons and the plot, as for the table
        layout.addLayout(controls)
        layout.addWidget(self.stack, stretch=1)

    def draw(self):
        """(Re)draw after a setting changed, or show why it can't be."""
        self._update_settings()
        problem = self.check_inputs()
        self.message.setText(problem or "")
        if problem:
            self.stack.setCurrentWidget(self.message)
            return
        if self.plot is not None:
            self.stack.setCurrentWidget(self.plot)
        self._draw()

    def _update_settings(self):
        """Enable or disable settings that depend on others (e.g. a column to sum)."""

    def _draw(self):
        """Set up the axes etc. for the current settings, then `_redraw` the data."""
        self._redraw()

    def _redraw(self):
        """Draw the data for the current filters (`self.passing`)."""

    def _drawable(self) -> bool:
        return self.plot is not None and self.check_inputs() is None

    # --- helpers --------------------------------------------------------------------------

    def set_axis(self, side: str, key: str | None, log: bool = False):
        """Label the `side` axis with column `key`, using date ticks for a date
        column and log ticks when `log` (values must already be log10'd)."""
        plot_item = self.plot.getPlotItem()
        is_date = key is not None and self.columns.kinds.get(key) == DATE
        if isinstance(plot_item.getAxis(side), pg.DateAxisItem) != is_date:
            axis = (
                pg.DateAxisItem(orientation=side, utcOffset=0)
                if is_date
                else pg.AxisItem(orientation=side)
            )
            plot_item.setAxisItems({side: axis})
            axis.setZValue(-1)  # behind the data, as in `style_plot`
            plot_item.showGrid(x=True, y=True, alpha=0.3)
        plot_item.getAxis(side).setLabel(key or "")
        if side == "bottom":
            plot_item.setLogMode(x=log)
        else:
            plot_item.setLogMode(y=log)

    def describe_row(self, row: int, keys: list[str]) -> str:
        """`row` for the status bar: its ID and its values of `keys`."""
        values = []
        for key in dict.fromkeys(k for k in keys if k):
            if self.columns.kinds.get(key) in (NUMBER, DATE):
                values.append(
                    f"{key} {self.columns.format(key, self.columns.numbers(key)[row])}"
                )
            else:
                values.append(f"{key} {self.df[key][row]}")
        return f"{self.df['id'][row]}: " + ", ".join(values)

    # --- what the dashboard calls ----------------------------------------------------------

    def set_mouse_mode(self, mode: int):
        """Whether left-drag zooms (`pg.ViewBox.RectMode`) or pans (`PanMode`)."""
        if self.view_box is not None:
            self.view_box.setMouseMode(mode)

    def set_passing(self, passing: np.ndarray):
        """Which rows pass the filters (by row index)."""
        self.passing = passing
        if self._drawable():
            self._redraw()

    def set_selected(self, rows: set[int]):
        self.selected_rows = set(rows)

    def show_hovered(self, rows: set[int]):
        """Mark `rows`, hovered somewhere else (e.g. in the table), or none when empty."""

    def view_ranges(self) -> list[tuple[str, object, object]]:
        """The (column, low, high) ranges in view, which the table is narrowed to."""
        return []
