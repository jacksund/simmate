from typing import Callable

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.theme import rgba
from simmate.desktop.widgets.button import PrimaryButton, button_style
from simmate.desktop.widgets.compound_table import NUMERIC_COLUMNS, CompoundTableModel
from simmate.desktop.widgets.inputs import StyledComboBox, input_style
from simmate.desktop.widgets.ketcher import KetcherWidget
from simmate.desktop.widgets.plot_toolbar import reset_icon
from simmate.toolkit.dataframes import MoleculeDataFrame


def filter_style() -> str:
    return f"""
#panelTitle {{ color: {theme.MUTED_COLOR}; font-weight: bold; }}
#rangeSep {{ color: palette(placeholder-text); }}
/* see-through, so the window shows behind the panel like the rest of the app */
#filterScroll, #filterContent {{ background: transparent; }}
/* rows changed from their defaults (i.e. actually filtering) */
QLabel[modified="true"] {{ color: {theme.PRIMARY_COLOR}; }}
QLineEdit[modified="true"], QComboBox[modified="true"],
QDoubleSpinBox[modified="true"] {{
    border-color: {theme.PRIMARY_COLOR};
    background: {rgba(theme.PRIMARY_COLOR, theme.HIGHLIGHT_ALPHA)};
}}
"""


class FilterPanel(QWidget):
    """The dashboard's filter column: a substructure sketcher with column filters below.

    Rows changed from their defaults are highlighted, with a button to reset just that row.

    `filters_changed` fires whenever anything changes; read the new state with `filters()`.
    `query_changed` also fires (first) when the sketched substructure changes.
    """

    filters_changed = Signal()
    query_changed = Signal(object)

    SKETCHER_HEIGHT = 380
    # Inputs otherwise size to their widest possible value (e.g. a min/max box's
    # ±1e6 range, or the longest series name), which overflows a narrow panel.
    SPIN_MIN_WIDTH = 50  # px
    COMBO_MIN_CHARACTERS = 6

    def __init__(self, mdf: MoleculeDataFrame):
        super().__init__()
        self.mdf = mdf
        self.query = None
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
        self.sketcher = KetcherWidget()
        self.sketcher.setFixedHeight(self.SKETCHER_HEIGHT)
        self.sketcher.mol_changed.connect(self._on_query_changed)

        # --- column filters -------------------------------------------------------------
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ID, series or SMILES…")
        self.search_input.setClearButtonEnabled(True)
        # refilter once typing pauses, not on every keystroke
        self.search_timer = QTimer(self, singleShot=True, interval=150)
        self.search_timer.timeout.connect(self.filters_changed)
        self.search_input.textChanged.connect(self.search_timer.start)

        self.series_combo = StyledComboBox()
        self.series_combo.addItems(
            ["All", *self.mdf.df["series"].unique().sort().to_list()]
        )
        self.status_combo = StyledComboBox()
        self.status_combo.addItems(["All", "Active", "Inactive"])
        for combo in (self.series_combo, self.status_combo):
            combo.setSizeAdjustPolicy(
                StyledComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            combo.setMinimumContentsLength(self.COMBO_MIN_CHARACTERS)
            combo.currentIndexChanged.connect(self.filters_changed)

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
            row = _FilterRow(QLabel(label), inputs or [field], is_default, reset)
            row.button.setToolTip(f"Reset {label.lower()}")
            row.button.clicked.connect(lambda: self._reset_row(row))
            index = form.rowCount()
            form.addWidget(row.label, index, 0, Qt.AlignmentFlag.AlignVCenter)
            form.addWidget(field, index, 1)
            form.addWidget(row.button, index, 2)
            self.rows.append(row)

        def reset_search():
            self.search_input.clear()
            self.search_timer.stop()  # the cleared search would emit again

        add_row(
            "Search",
            self.search_input,
            lambda: not self.search_input.text(),
            reset_search,
        )
        for label, combo in [
            ("Series", self.series_combo),
            ("Status", self.status_combo),
        ]:
            add_row(
                label,
                combo,
                lambda c=combo: c.currentIndex() == 0,
                lambda c=combo: c.setCurrentIndex(0),
            )

        headers = {key: header for header, key in CompoundTableModel.COLUMNS}
        self.range_inputs: dict[str, tuple[QDoubleSpinBox, QDoubleSpinBox]] = {}
        # Each min/max box defaults to the full range of its column (i.e. no
        # filtering), read back from the boxes so it's rounded as they show it.
        self.range_defaults: dict[str, tuple[float, float]] = {}
        for key in NUMERIC_COLUMNS:
            spins = (QDoubleSpinBox(), QDoubleSpinBox())
            range_row = QWidget()
            range_layout = QHBoxLayout(range_row)
            range_layout.setContentsMargins(0, 0, 0, 0)
            range_layout.setSpacing(6)
            for i, spin in enumerate(spins):
                spin.setDecimals(2)
                spin.setRange(-1e6, 1e6)
                spin.setMinimumWidth(self.SPIN_MIN_WIDTH)
                # arrow keys and the mouse wheel still step the value
                spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
                # apply when typing is done, not on every keystroke
                spin.setKeyboardTracking(False)
                spin.valueChanged.connect(self.filters_changed)
                if i:
                    range_layout.addWidget(QLabel("to", objectName="rangeSep"))
                range_layout.addWidget(spin, stretch=1)
            self.range_inputs[key] = spins
            add_row(
                headers[key],
                range_row,
                lambda k=key: self._range_values(k) == self.range_defaults[k],
                lambda k=key: self._reset_range(k),
                inputs=list(spins),
            )

        # --- layout -------------------------------------------------------------------
        content = QWidget(objectName="filterContent")
        content_layout = QVBoxLayout(content)
        # breathing room from the window's edges and the pull tab's line (right)
        content_layout.setContentsMargins(8, 8, 12, 8)
        content_layout.addLayout(header)
        content_layout.addSpacing(8)
        content_layout.addWidget(self.sketcher)
        content_layout.addSpacing(20)
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
        """The current filters, as keyword arguments for `CompoundFilterProxy.set_filters`."""
        return dict(
            text=self.search_input.text(),
            series=_choice(self.series_combo),
            status=_choice(self.status_combo),
            query=self.query,
            value_ranges=[
                (key, low.value(), high.value())
                for key, (low, high) in self.range_inputs.items()
            ],
        )

    def reset_filters(self):
        """Clear the sketch and every column filter."""
        # The sketcher reports its (now empty) canvas back through `mol_changed`.
        self.sketcher.clear()
        self._reset_form()

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

    def _range_values(self, key: str) -> tuple[float, float]:
        low, high = self.range_inputs[key]
        return low.value(), high.value()

    def _reset_range(self, key: str):
        low, high = self.range_inputs[key]
        column = self.mdf.df[key]
        low.setValue(column.min())
        high.setValue(column.max())
        self.range_defaults.setdefault(key, self._range_values(key))

    def _update_modified(self):
        for row in self.rows:
            row.set_modified(not row.is_default())

    def _on_query_changed(self, query):
        self.query = query
        self.query_changed.emit(query)
        self.filters_changed.emit()


class _FilterRow:
    """One row of the filter form: its label, inputs, and reset button."""

    ICON_SIZE = 14  # px

    def __init__(
        self,
        label: QLabel,
        inputs: list[QWidget],
        is_default: Callable[[], bool],
        reset: Callable[[], None],
    ):
        self.label = label
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

    def set_modified(self, modified: bool):
        """Highlight the row (via filter_style) and show its reset button."""
        self.button.setVisible(modified)
        for widget in [self.label, *self.inputs]:
            if widget.property("modified") != modified:
                widget.setProperty("modified", modified)
                # stylesheets only re-read dynamic properties on a re-polish
                widget.style().unpolish(widget)
                widget.style().polish(widget)


def _choice(combo: StyledComboBox) -> str | None:
    """The combo's text, or None while it's on its first ("All") item."""
    return combo.currentText() if combo.currentIndex() else None
