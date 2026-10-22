import math
from collections.abc import Callable
from datetime import date

from PySide6.QtCore import QDate, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.data import CATEGORY, DATE, NUMBER, ToolkitDataset
from simmate.desktop.data.columns import to_date, to_seconds
from simmate.desktop.theme import rgba
from simmate.desktop.widgets.button import PrimaryButton, button_style
from simmate.desktop.widgets.compound_table import scroll_bar_style
from simmate.desktop.widgets.inputs import StyledCheckBox, input_style
from simmate.desktop.widgets.ketcher import KetcherWidget
from simmate.desktop.widgets.plot_toolbar import SettingsButton, reset_icon
from simmate.desktop.widgets.status import note_label


def filter_style() -> str:
    return f"""
#panelTitle {{ color: {theme.MUTED_COLOR}; font-weight: bold; }}
#rangeSep {{ color: palette(placeholder-text); }}
/* see-through, so the window shows behind the panel like the rest of the app */
#filterScroll, #filterContent {{ background: transparent; }}
/* date boxes, styled like the other inputs (see input_style) */
QDateEdit {{
    background: palette(base); border: 1px solid palette(mid);
    border-radius: 6px; padding: 4px 8px; min-height: 18px;
}}
QDateEdit:hover, QDateEdit:focus {{ border-color: {theme.PRIMARY_COLOR}; }}
QDateEdit::drop-down {{ border: none; width: 0; }}
/* min/max boxes without step arrows (the arrow keys and mouse wheel still step).
   Hidden here rather than with NoButtons, which (under a stylesheet) squeezes the
   box's text field to nothing. */
#rangeBox::up-button, #rangeBox::down-button {{ width: 0; border: none; }}
#rangeBox::up-arrow, #rangeBox::down-arrow {{ image: none; width: 0; }}
/* rows changed from their defaults (i.e. actually filtering) */
QLabel[modified="true"] {{ color: {theme.PRIMARY_COLOR}; }}
QLineEdit[modified="true"], QDoubleSpinBox[modified="true"],
QDateEdit[modified="true"], QToolButton[modified="true"] {{
    border-color: {theme.PRIMARY_COLOR};
    background: {rgba(theme.PRIMARY_COLOR, theme.HIGHLIGHT_ALPHA)};
}}
"""


class FilterPanel(QWidget):
    """The dashboard's filter column: a substructure sketcher with column filters below.

    The filters are made from the dataset's columns (see `DataColumns`): one search
    box over its text columns, a checklist for each category column, and a min/max
    pair for each number or date column. The sketcher only shows for datasets with
    molecules. Rows changed from their defaults are highlighted, with a button to
    reset just that row.

    Substructure searches need the dataset's index (see `ToolkitDataset`), which is
    built in the background; a sketch made before it's ready applies once
    `set_index_ready` is called.

    `filters_changed` fires whenever anything changes; read the new state with `filters()`.
    `query_changed` also fires (first) when the sketched substructure changes.
    """

    filters_changed = Signal()
    query_changed = Signal(object)

    SKETCHER_HEIGHT = 380
    # Inputs otherwise size to their widest possible value (e.g. a min/max box's
    # ±1e15 range), which overflows a narrow panel.
    SPIN_MIN_WIDTH = 50  # px
    # Above this many filter rows, a box to find a column's filter shows above them.
    ROW_SEARCH_MIN = 12
    # How many searched columns the search box's placeholder names.
    PLACEHOLDER_COLUMNS = 3

    def __init__(self, dataset: ToolkitDataset):
        super().__init__()
        self.dataset = dataset
        self.columns = dataset.columns
        self.query = None
        self.index_ready = not dataset.has_molecules
        self.setStyleSheet(filter_style() + input_style())

        # --- header -------------------------------------------------------------------
        title = QLabel("Filters", objectName="panelTitle")
        font = title.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        title.setFont(font)
        reset_button = PrimaryButton("Reset filters", muted=True)
        reset_button.setToolTip("Clear the sketch and every filter below it")
        reset_button.clicked.connect(self.reset_filters)

        header = QHBoxLayout()
        header.addWidget(title, stretch=1)
        header.addWidget(reset_button)

        # --- substructure sketcher ----------------------------------------------------
        self.sketcher = None
        self.index_note = note_label("")
        self.index_note.hide()
        if dataset.has_molecules:
            self.sketcher = KetcherWidget()
            self.sketcher.setFixedHeight(self.SKETCHER_HEIGHT)
            self.sketcher.mol_changed.connect(self._on_query_changed)

        # --- column filters -------------------------------------------------------------
        # A grid rather than a QFormLayout, which won't center labels on taller fields.
        # Columns: label, field, and the row's reset button.
        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.setColumnStretch(1, 1)
        self.rows: list[_FilterRow] = []

        def add_row(
            label: str,
            field: QWidget,
            is_default: Callable[[], bool],
            reset: Callable[[], None],
            inputs: list[QWidget] | None = None,
        ):
            row = _FilterRow(QLabel(label), field, inputs or [field], is_default, reset)
            row.label.setToolTip(label)
            row.button.setToolTip(f"Reset {label}")
            row.button.clicked.connect(lambda: self._reset_row(row))
            index = form.rowCount()
            form.addWidget(row.label, index, 0, Qt.AlignmentFlag.AlignVCenter)
            form.addWidget(field, index, 1)
            form.addWidget(row.button, index, 2)
            self.rows.append(row)

        self.search_input = QLineEdit()
        searched = self.columns.searched
        shown = ", ".join(searched[: self.PLACEHOLDER_COLUMNS])
        more = "…" if len(searched) > self.PLACEHOLDER_COLUMNS else ""
        self.search_input.setPlaceholderText(f"{shown}{more}")
        self.search_input.setToolTip("Searches " + ", ".join(searched))
        self.search_input.setClearButtonEnabled(True)
        # refilter once typing pauses, not on every keystroke
        self.search_timer = QTimer(self, singleShot=True, interval=150)
        self.search_timer.timeout.connect(self.filters_changed)
        self.search_input.textChanged.connect(self.search_timer.start)

        def reset_search():
            self.search_input.clear()
            self.search_timer.stop()  # the cleared search would emit again

        if searched:
            add_row(
                "Search",
                self.search_input,
                lambda: not self.search_input.text(),
                reset_search,
            )

        self.category_inputs: dict[str, _MultiChoice] = {}
        for key in self.columns.of_kind(CATEGORY):
            choice = _MultiChoice(self.columns.codes(key)[1])
            choice.changed.connect(self.filters_changed)
            self.category_inputs[key] = choice
            add_row(
                key,
                choice,
                lambda c=choice: not c.chosen(),
                lambda c=choice: c.set_chosen([]),
                inputs=[choice.button],
            )

        # Each min/max pair defaults to the full range of its column (i.e. no
        # filtering), read back from the boxes so it's rounded as they show it.
        self.range_inputs: dict[str, tuple[QWidget, QWidget]] = {}
        self.range_defaults: dict[str, tuple] = {}
        for key in self.columns.of_kind(NUMBER, DATE):
            if self.columns.bounds(key) is None:
                continue  # all nulls: nothing to filter
            is_date = self.columns.kinds[key] == DATE
            boxes = (
                (self._date_box(), self._date_box())
                if is_date
                else (self._spin_box(), self._spin_box())
            )
            range_row = QWidget()
            range_layout = QHBoxLayout(range_row)
            range_layout.setContentsMargins(0, 0, 0, 0)
            range_layout.setSpacing(6)
            for i, box in enumerate(boxes):
                if i:
                    range_layout.addWidget(QLabel("to", objectName="rangeSep"))
                range_layout.addWidget(box, stretch=1)
            self.range_inputs[key] = boxes
            add_row(
                key,
                range_row,
                lambda k=key: self._range_values(k) == self.range_defaults[k],
                lambda k=key: self._reset_range(k),
                inputs=list(boxes),
            )

        # Long lists of filters (e.g. wide datasets) get a box to find a column's.
        self.row_search = QLineEdit()
        self.row_search.setPlaceholderText("Find a column…")
        self.row_search.setClearButtonEnabled(True)
        self.row_search.textChanged.connect(self._show_matching_rows)
        self.row_search.setVisible(len(self.rows) > self.ROW_SEARCH_MIN)

        # --- layout -------------------------------------------------------------------
        content = QWidget(objectName="filterContent")
        content_layout = QVBoxLayout(content)
        # breathing room from the window's edges and the pull tab's line (right)
        content_layout.setContentsMargins(8, 8, 12, 8)
        content_layout.addLayout(header)
        content_layout.addSpacing(8)
        if self.sketcher is not None:
            content_layout.addWidget(self.sketcher)
            content_layout.addWidget(self.index_note)
            content_layout.addSpacing(20)
        content_layout.addWidget(self.row_search)
        content_layout.addLayout(form)
        content_layout.addStretch()

        # Scrolls rather than squashing the fixed-height sketcher on short windows.
        scroll = QScrollArea(objectName="filterScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        scroll.viewport().setAutoFillBackground(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.filters_changed.connect(self._update_modified)
        self._reset_form()

    def filters(self) -> dict:
        """The current filters, as keyword arguments for `CompoundFilterProxy.set_filters`.
        Filters left at their defaults are left out, so they keep rows with nulls."""
        value_ranges = []
        for key in self.range_inputs:
            values = self._range_values(key)
            if values != self.range_defaults[key]:
                value_ranges.append((key, *self._range_numbers(key)))
        return dict(
            text=self.search_input.text(),
            # held back until the index can run it
            query=self.query if self.index_ready else None,
            value_ranges=value_ranges,
            categories={
                key: choice.chosen()
                for key, choice in self.category_inputs.items()
                if choice.chosen()
            },
        )

    def set_index_progress(self, done: int, total: int):
        """Show how far along the substructure index is."""
        if self.sketcher is None:
            return
        percent = f" ({100 * done // total}%)" if total else ""
        self.index_note.setText(
            f"Indexing structures for substructure search…{percent}"
        )
        self.index_note.show()

    def set_index_ready(self, ready: bool = True, error: str = ""):
        """The substructure index is built (or failed, with `error`), so a sketched
        query can apply."""
        self.index_ready = ready
        if error:
            self.index_note.setText(f"Substructure search is unavailable: {error}")
            self.index_note.show()
            return
        self.index_note.hide()
        if ready and self.query is not None:
            self.query_changed.emit(self.query)
            self.filters_changed.emit()

    def reset_filters(self):
        """Clear the sketch and every column filter."""
        # The sketcher reports its (now empty) canvas back through `mol_changed`.
        if self.sketcher is not None:
            self.sketcher.clear()
        self._reset_form()

    def _spin_box(self) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(objectName="rangeBox")  # no arrows, see filter_style
        spin.setDecimals(2)
        spin.setRange(-1e15, 1e15)
        spin.setMinimumWidth(self.SPIN_MIN_WIDTH)
        # apply when typing is done, not on every keystroke
        spin.setKeyboardTracking(False)
        spin.valueChanged.connect(self.filters_changed)
        return spin

    def _date_box(self) -> QDateEdit:
        box = QDateEdit()
        box.setDisplayFormat("yyyy-MM-dd")
        box.setCalendarPopup(True)
        box.setMinimumWidth(self.SPIN_MIN_WIDTH)
        box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        box.setKeyboardTracking(False)
        box.dateChanged.connect(self.filters_changed)
        return box

    def _reset_form(self):
        # Every input forwards its changes through `filters_changed`, so muting
        # it gives a single emit for the whole reset.
        self.blockSignals(True)
        for row in self.rows:
            row.reset()
        self.blockSignals(False)
        self.filters_changed.emit()

    def _reset_row(self, row: "_FilterRow"):
        # muted like `_reset_form`, since a range row resets two boxes
        self.blockSignals(True)
        row.reset()
        self.blockSignals(False)
        self.filters_changed.emit()

    def _range_values(self, key: str) -> tuple:
        low, high = self.range_inputs[key]
        if isinstance(low, QDateEdit):
            return low.date(), high.date()
        return low.value(), high.value()

    def _range_numbers(self, key: str) -> tuple[float, float]:
        """The range's bounds, as `DataColumns.numbers` gives the column's values."""
        low, high = self._range_values(key)
        if isinstance(low, QDate):
            # through the end of the last day
            return to_seconds(low.toPython()), to_seconds(high.toPython()) + 86_399
        return low, high

    def _reset_range(self, key: str):
        low_box, high_box = self.range_inputs[key]
        low, high = self.columns.bounds(key)
        if isinstance(low_box, QDateEdit):
            low_box.setDate(_qdate(to_date(low)))
            high_box.setDate(_qdate(to_date(high)))
        else:
            # rounded out, so the default range keeps the very smallest and largest
            low_box.setValue(_round_down(low))
            high_box.setValue(_round_up(high))
        self.range_defaults.setdefault(key, self._range_values(key))

    def _update_modified(self):
        for row in self.rows:
            row.set_modified(not row.is_default())

    def _show_matching_rows(self, text: str):
        text = text.lower()
        for row in self.rows:
            row.set_visible(text in row.label.text().lower())

    def _on_query_changed(self, query):
        self.query = query
        if not self.index_ready:
            if query is not None:
                self.set_index_progress(0, 0)
            return  # applied once the index is ready
        self.query_changed.emit(query)
        self.filters_changed.emit()


class _MultiChoice(QWidget):
    """A button that opens a checklist of `options`, to pick any number of them.

    Picking none (the default) means no filter, and the button reads "All" in grey;
    it turns the primary color once something is picked. `changed` fires as boxes
    are checked or unchecked.
    """

    changed = Signal()

    MAX_LABEL = 24  # characters of the chosen options shown on the button

    def __init__(self, options: list[str]):
        super().__init__()
        self.checkboxes: dict[str, StyledCheckBox] = {}
        content = QWidget()
        content.setStyleSheet(input_style() + scroll_bar_style())
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)
        clear = PrimaryButton("Clear", muted=True)
        clear.clicked.connect(lambda: self.set_chosen([]))
        content_layout.addWidget(clear)
        for option in options:
            checkbox = StyledCheckBox(option)
            checkbox.toggled.connect(self._on_toggled)
            content_layout.addWidget(checkbox)
            self.checkboxes[option] = checkbox

        self.button = SettingsButton(content, tooltip="Choose values to keep", text=" ")
        self.button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button)
        self._update_text()

    def chosen(self) -> list[str]:
        return [option for option, box in self.checkboxes.items() if box.isChecked()]

    def set_chosen(self, options: list[str]):
        for option, box in self.checkboxes.items():
            box.blockSignals(True)
            box.setChecked(option in options)
            box.blockSignals(False)
        self._on_toggled()

    def _on_toggled(self, *_):
        self._update_text()
        self.changed.emit()

    def _update_text(self):
        chosen = self.chosen()
        text = ", ".join(chosen) if chosen else "All"
        if len(text) > self.MAX_LABEL:
            text = f"{len(chosen)} selected"
        self.button.setText(text)
        # grey while it isn't filtering, read by button_style
        if self.button.property("muted") != (not chosen):
            self.button.setProperty("muted", not chosen)
            self.button.style().unpolish(self.button)
            self.button.style().polish(self.button)


class _FilterRow:
    """One row of the filter form: its label, field, inputs, and reset button."""

    ICON_SIZE = 14  # px

    def __init__(
        self,
        label: QLabel,
        field: QWidget,
        inputs: list[QWidget],
        is_default: Callable[[], bool],
        reset: Callable[[], None],
    ):
        self.label = label
        self.field = field
        self.inputs = inputs
        self.is_default = is_default
        self.reset = reset

        self.button = QToolButton()
        self.button.setProperty("muted", True)  # grey, read by button_style
        self.button.setStyleSheet(button_style())
        self.button.setIcon(reset_icon(self.ICON_SIZE))
        self.button.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        # keep its space while hidden, so fields don't jump when it appears
        policy = self.button.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.button.setSizePolicy(policy)
        self.button.hide()
        self.modified = False

    def set_modified(self, modified: bool):
        """Highlight the row (via filter_style) and show its reset button."""
        self.modified = modified
        self.button.setVisible(modified and not self.label.isHidden())
        for widget in [self.label, *self.inputs]:
            if widget.property("modified") != modified:
                widget.setProperty("modified", modified)
                # stylesheets only re-read dynamic properties on a re-polish
                widget.style().unpolish(widget)
                widget.style().polish(widget)

    def set_visible(self, visible: bool):
        """Show or hide the whole row (e.g. when finding a column's filter)."""
        self.label.setVisible(visible)
        self.field.setVisible(visible)
        self.button.setVisible(visible and self.modified)


def _round_down(value: float) -> float:
    """`value` rounded down to the spin boxes' 2 decimals."""
    return math.floor(value * 100) / 100


def _round_up(value: float) -> float:
    return math.ceil(value * 100) / 100


def _qdate(value: date) -> QDate:
    return QDate(value.year, value.month, value.day)
