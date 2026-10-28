import html
import math
import time

import numpy as np
from PySide6.QtCore import QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.data import ToolkitDataset
from simmate.desktop.data.analyses import (
    ANALYSES,
    CHOICE,
    COLUMN,
    COLUMNS,
    FINGERPRINT_FEATURES,
    INTEGER,
    Analysis,
    AnalysisResult,
    Setting,
    format_number,
    join_names,
)
from simmate.desktop.data.features import SLOW_FEATURE_ROWS
from simmate.desktop.theme import rgba
from simmate.desktop.widgets.background import BackgroundTask
from simmate.desktop.widgets.button import PrimaryButton, button_style
from simmate.desktop.widgets.compound_table import (
    SortHeader,
    scroll_bar_style,
    table_style,
)
from simmate.desktop.widgets.confirm_dialog import confirm
from simmate.desktop.widgets.inputs import StyledComboBox, input_style
from simmate.desktop.widgets.multi_choice import MultiChoice
from simmate.desktop.widgets.plot_toolbar import HelpButton, close_icon
from simmate.desktop.widgets.status import (
    callout_style,
    loading_bar,
    note_label,
    progress_bar_style,
)

# The role holding a result table row's place in `AnalysisResult.table`, which
# sorting the table doesn't change.
ROW_ROLE = Qt.ItemDataRole.UserRole

# How each level of `AnalysisResult.verdict` reads, and its color.
VERDICTS = {
    "strong": ("Strong", theme.SUCCESS_COLOR),
    "moderate": ("Moderate", theme.PRIMARY_COLOR),
    "weak": ("Weak", theme.MUTED_COLOR),
    "none": ("No skill", theme.ERROR_COLOR),
}


def analyze_style() -> str:
    return f"""
#panelTitle {{ color: {theme.MUTED_COLOR}; font-weight: bold; }}
#sectionTitle {{ color: {theme.MUTED_COLOR}; font-weight: 600; }}
/* see-through, so the window shows behind the panel like the rest of the app */
#analyzeScroll, #analyzeContent {{ background: transparent; }}
#resultCard {{ border: 1px solid palette(mid); border-radius: 8px; }}
#cardSubtitle {{ color: {theme.MUTED_LIGHTER}; font-size: 11px; }}
/* small headings within a card, e.g. above its bars */
#cardHeading {{ color: {theme.MUTED_COLOR}; font-size: 11px; font-weight: 600; }}
#scoreTile {{
    background: {rgba(theme.PRIMARY_COLOR, theme.HIGHLIGHT_ALPHA)};
    border-radius: 6px;
}}
#scoreValue {{ font-size: 16px; font-weight: 600; }}
#scoreName, #detailLabel, #barValue {{ color: {theme.MUTED_COLOR}; font-size: 11px; }}
#equation {{
    background: {rgba(theme.MUTED_COLOR, 20)}; border-radius: 6px; padding: 6px 8px;
}}
{scroll_bar_style()}"""


class AnalyzePanel(QWidget):
    """The dashboard's Analyze column: analyses of every row at once (see
    `ANALYSES`), such as fitting a model that predicts one column from others.

    Pick one from the list, fill in its form, then "Run" works it out in the
    background. Those tagged slow ask first on datasets of more than
    `SLOW_FEATURE_ROWS` rows. Each run's result shows as a card (newest first), so
    runs can be compared, and any columns it gives are added to the dataset.

    - `columns_added(added, replaced)`: columns are in the dataset (see
      `ToolkitDataset.add_columns`).
    - `rows_hovered(rows)`: a result's table row behind these dataset rows is
      hovered (empty once off it).
    - `rows_selected(rows)`: a result's table row behind these dataset rows was
      clicked.
    - `plot_requested(name, config)`: a result's plot button was clicked, for a
      plot of this name (see `PLOT_TYPES`) with these settings.
    """

    columns_added = Signal(object, object)
    rows_hovered = Signal(object)
    rows_selected = Signal(object)
    plot_requested = Signal(str, object)

    def __init__(self, dataset: ToolkitDataset):
        super().__init__()
        self.dataset = dataset
        self.task: BackgroundTask | None = None
        self.started = 0.0  # when the run began (perf_counter)
        self.setStyleSheet(analyze_style() + input_style())

        title = QLabel("Analyze", objectName="panelTitle")
        font = title.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        title.setFont(font)
        # the analyses, under a heading (that can't be picked) per section
        self.picker = StyledComboBox()
        for analysis in ANALYSES:
            if self.picker.findText(analysis.section) < 0:
                self.picker.addItem(analysis.section)
                heading = self.picker.model().item(self.picker.count() - 1)
                heading.setEnabled(False)
                font = heading.font()
                font.setBold(True)
                heading.setFont(font)
            self.picker.addItem(analysis.name, analysis)
        self.about = note_label("")

        # --- the forms (only the picked one shows), then the results ------------------
        content = QWidget(objectName="analyzeContent")
        content_layout = QVBoxLayout(content)
        # breathing room from the window's edges and the pull tab's line (right)
        content_layout.setContentsMargins(8, 0, 12, 8)
        content_layout.setSpacing(8)
        self.forms: dict[str, _AnalysisForm] = {}
        for analysis in ANALYSES:
            form = _AnalysisForm(analysis, dataset)
            form.hide()
            content_layout.addWidget(form)
            self.forms[analysis.name] = form
        content_layout.addSpacing(12)
        self.results_heading = QLabel("Results", objectName="sectionTitle")
        self.results_heading.hide()
        content_layout.addWidget(self.results_heading)
        self.results_layout = QVBoxLayout()
        self.results_layout.setSpacing(8)
        content_layout.addLayout(self.results_layout)
        content_layout.addStretch()

        self.scroll = QScrollArea(objectName="analyzeScroll")
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(content)
        self.scroll.viewport().setAutoFillBackground(False)

        # --- footer: stays below the list ---------------------------------------------
        self.loading_bar = loading_bar()
        self.note = note_label("")  # while a run is going
        self.note.hide()
        # why the last run failed, in a red callout
        self.error = QLabel(wordWrap=True, textFormat=Qt.TextFormat.RichText)
        self.error.setStyleSheet(callout_style(theme.ERROR_COLOR))
        self.error.hide()
        self.run_button = PrimaryButton("Run", filled=True)
        self.run_button.clicked.connect(self.run)

        header = QVBoxLayout()
        header.setContentsMargins(8, 8, 12, 8)
        header.setSpacing(12)
        header.addWidget(title)
        header.addWidget(self.picker)
        header.addWidget(self.about)
        footer = QVBoxLayout()
        footer.setContentsMargins(8, 8, 12, 8)
        footer.setSpacing(8)
        footer.addWidget(self.loading_bar)
        footer.addWidget(self.note)
        footer.addWidget(self.error)
        footer.addWidget(self.run_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header)
        layout.addWidget(self.scroll, stretch=1)
        layout.addLayout(footer)

        self.picker.currentIndexChanged.connect(self._show_form)
        self.picker.setCurrentIndex(1)  # the first analysis, after its heading

    @property
    def analysis(self) -> Analysis:
        """The picked analysis."""
        return self.picker.currentData()

    def run(self):
        """Work out the picked analysis in the background, then show its result."""
        analysis = self.analysis
        if (
            analysis.slow
            and self.dataset.height > SLOW_FEATURE_ROWS
            and not confirm(
                self,
                "Run on a large dataset?",
                f"{analysis.name} doesn't scale well. This dataset has "
                f"{self.dataset.height:,} rows, more than {SLOW_FEATURE_ROWS:,}, so it "
                "may take a long time and use a lot of memory.",
                yes="Run anyway",
                no="Cancel",
            )
        ):
            return
        values = self.forms[analysis.name].values()
        dataset = self.dataset
        # Not parented to the panel, which is deleted if the dataset is closed
        # mid-run. Its connections to the panel's methods go with the panel, so the
        # result is then dropped.
        self.task = BackgroundTask(lambda _: analysis.run(dataset, **values))
        self.task.finished.connect(self._on_finished)
        self.task.failed.connect(self._on_failed)
        self.note.setText(f"Running {analysis.name}…")
        self._set_running(True)
        self.started = time.perf_counter()
        self.task.start()

    def add_columns(self, added: list[str], replaced: list[str]):
        """Offer columns just added to the dataset in every form."""
        for form in self.forms.values():
            form.refresh_columns()

    def _show_form(self, index: int):
        for name, form in self.forms.items():
            form.setVisible(name == self.analysis.name)
        self.about.setText(self.analysis.description)

    def _on_finished(self, result: AnalysisResult):
        self.task = None
        self._set_running(False)
        added = []
        if result.columns is not None:
            added = result.columns.columns
            self.columns_added.emit(*self.dataset.add_columns(result.columns))
        elapsed = time.perf_counter() - self.started
        took = (
            f"{elapsed:.1f}s"
            if elapsed < 60
            else f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        )
        card = _ResultCard(result, took, added)
        card.rows_hovered.connect(self.rows_hovered)
        card.rows_selected.connect(self.rows_selected)
        card.plot_requested.connect(self.plot_requested)
        card.closed.connect(lambda: self._remove_card(card))
        self.results_layout.insertWidget(0, card)
        self.results_heading.show()
        # once it's laid out
        QTimer.singleShot(0, lambda: self.scroll.ensureWidgetVisible(card))

    def _on_failed(self, error: str):
        self.task = None
        self._set_running(False)
        self.error.setText(
            f"<b>✗ Couldn't run {html.escape(self.analysis.name)}</b><br>"
            f"{html.escape(error)}"
        )
        self.error.show()

    def _remove_card(self, card: "_ResultCard"):
        self.results_layout.removeWidget(card)
        card.deleteLater()
        self.results_heading.setVisible(self.results_layout.count() > 0)

    def _set_running(self, running: bool):
        self.loading_bar.setVisible(running)
        self.note.setVisible(running)
        self.run_button.setEnabled(not running)
        if running:
            self.error.hide()


class _AnalysisForm(QWidget):
    """The inputs of one analysis, a row for each of its `Setting`s: its label,
    its input, and a "?" button explaining it."""

    def __init__(self, analysis: Analysis, dataset: ToolkitDataset):
        super().__init__()
        self.analysis = analysis
        self.dataset = dataset
        self.inputs: dict[str, QWidget] = {}
        # the section of a COLUMNS setting's list that columns go in (see MultiChoice)
        self.column_sections: dict[str, str | None] = {}
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)
        layout.setColumnStretch(1, 1)
        for row, setting in enumerate(analysis.settings):
            if setting.kind == COLUMN:
                widget = StyledComboBox()
                self._fill_columns(widget, setting)
            elif setting.kind == COLUMNS:
                columns = dataset.columns.of_kind(*setting.column_kinds)
                if setting.fingerprints and dataset.has_molecules:
                    self.column_sections[setting.key] = "Columns"
                    options = {
                        "Fingerprints": list(FINGERPRINT_FEATURES),
                        "Columns": columns,
                    }
                else:
                    self.column_sections[setting.key] = None  # no headings
                    options = columns
                widget = MultiChoice(
                    options, placeholder="Choose…", tooltip="Choose any number"
                )
                for name, feature in FINGERPRINT_FEATURES.items():
                    if name in widget.checkboxes:
                        widget.checkboxes[name].setToolTip(feature.description)
                widget.set_chosen(setting.default)
            elif setting.kind == CHOICE:
                widget = StyledComboBox()
                widget.addItems(setting.choices)
                if setting.default is not None:
                    widget.setCurrentText(setting.default)
            elif setting.kind == INTEGER:
                widget = QSpinBox(
                    minimum=setting.minimum,
                    maximum=setting.maximum,
                    value=setting.default,
                )
            layout.addWidget(QLabel(setting.label), row, 0)
            layout.addWidget(widget, row, 1)
            if setting.help:
                layout.addWidget(HelpButton(setting.help), row, 2)
            self.inputs[setting.key] = widget

        # a list that leaves out another setting's column follows that setting
        for setting in analysis.settings:
            if setting.excluding:
                combo = self.inputs[setting.excluding]
                combo.currentTextChanged.connect(
                    lambda column, key=setting.key: self._exclude(key, column)
                )
                self._exclude(setting.key, combo.currentText())

    def values(self) -> dict:
        """Each setting's value, by its key, as the analysis's `run` takes them."""
        values = {}
        for setting in self.analysis.settings:
            widget = self.inputs[setting.key]
            if setting.kind == COLUMN:
                values[setting.key] = widget.currentText() or None
            elif setting.kind == COLUMNS:
                values[setting.key] = [
                    name
                    for name in widget.chosen()
                    if widget.checkboxes[name].isEnabled()
                ]
            elif setting.kind == CHOICE:
                values[setting.key] = widget.currentText()
            elif setting.kind == INTEGER:
                values[setting.key] = widget.value()
        return values

    def refresh_columns(self):
        """Offer columns added to the dataset since the form was made, keeping each
        current choice. New columns start unpicked, as they may come from an
        earlier result (e.g. a model's predictions)."""
        for setting in self.analysis.settings:
            widget = self.inputs[setting.key]
            if setting.kind == COLUMN:
                before = widget.currentText()
                self._fill_columns(widget, setting)
                if widget.currentText() != before:
                    # muted while refilling, so a list following it hasn't heard
                    widget.currentTextChanged.emit(widget.currentText())
            elif setting.kind == COLUMNS:
                widget.add_options(
                    self.dataset.columns.of_kind(*setting.column_kinds),
                    self.column_sections[setting.key],
                )

    def _fill_columns(self, combo: StyledComboBox, setting: Setting):
        """(Re)fill a COLUMN setting's choices, keeping its choice (or starting at
        its default, if there's such a column)."""
        current = combo.currentText() or setting.default
        options = self.dataset.columns.of_kind(*setting.column_kinds)
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(options)
        if current in options:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    def _exclude(self, key: str, column: str):
        """Make `column` (e.g. the one to predict) unpickable in the COLUMNS setting
        `key`, and unpick columns named after it (e.g. "pIC50_pred")."""
        choice = self.inputs[key]
        for name, box in choice.checkboxes.items():
            box.setEnabled(name != column)
            if column and (name == column or name.startswith(f"{column}_")):
                box.setChecked(False)


class _ResultCard(QFrame):
    """One run's result (see `AnalysisResult`), laid out to read at a glance: its
    title, score tiles and verdict up top, then its details, breakdowns (a
    confusion grid, bars, or a table), and plot button.

    Hovering or clicking a table row with dataset rows behind it emits
    `rows_hovered` or `rows_selected`. `closed` fires from its "×" button."""

    rows_hovered = Signal(object)
    rows_selected = Signal(object)
    plot_requested = Signal(str, object)
    closed = Signal()

    VISIBLE_ROWS = 8  # the table scrolls past this many rows
    ROW_HEIGHT = 28
    MAX_LABELS = 6  # labels a confusion grid can fit across the card
    NAME_WIDTH = 110  # px of a bar's or grid label's name, elided past this
    CLOSE_ICON_SIZE = 10  # px

    def __init__(self, result: AnalysisResult, took: str, added: list[str]):
        super().__init__(objectName="resultCard")
        self.result = result
        self.table: QTableWidget | None = None

        # --- header: title and when, then its help and close buttons --------------------
        title = QLabel(result.title, wordWrap=True)
        font = title.font()
        font.setPointSizeF(font.pointSizeF() * 1.15)
        font.setBold(True)
        title.setFont(font)
        subtitle = QLabel(
            " · ".join(filter(None, [result.subtitle, time.strftime("%H:%M"), took])),
            objectName="cardSubtitle",
        )
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header = QHBoxLayout()
        header.setSpacing(6)
        header.addLayout(titles, stretch=1)
        if result.help:
            header.addWidget(
                HelpButton(result.help), alignment=Qt.AlignmentFlag.AlignTop
            )
        # round and small, a pair with the "?"
        close_button = QToolButton()
        close_button.setProperty("muted", True)  # grey, read by button_style
        close_button.setStyleSheet(
            button_style()
            + f"QToolButton {{ padding: 0; border-radius: {HelpButton.SIZE // 2}px; }}"
        )
        close_button.setFixedSize(HelpButton.SIZE, HelpButton.SIZE)
        close_button.setIcon(close_icon(self.CLOSE_ICON_SIZE))
        close_button.setIconSize(QSize(self.CLOSE_ICON_SIZE, self.CLOSE_ICON_SIZE))
        close_button.setToolTip("Remove this result")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.closed)
        header.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignTop)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)
        layout.addLayout(header)

        # --- headline: score tiles, and what they add up to ------------------------------
        if result.scores:
            tiles = QHBoxLayout()
            tiles.setSpacing(6)
            for name, value in result.scores:
                tile = QFrame(objectName="scoreTile")
                tile_layout = QVBoxLayout(tile)
                tile_layout.setContentsMargins(4, 6, 4, 6)
                tile_layout.setSpacing(0)
                for text, object_name in [(value, "scoreValue"), (name, "scoreName")]:
                    label = QLabel(text, objectName=object_name)
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    tile_layout.addWidget(label)
                tiles.addWidget(tile, stretch=1)
            layout.addLayout(tiles)
        if result.verdict:
            level, why = result.verdict
            word, color = VERDICTS[level]
            layout.addWidget(
                QLabel(
                    f"<span style='color: {color};'>●&nbsp;<b>{word}</b></span>"
                    f"&nbsp; {html.escape(why)}",
                    wordWrap=True,
                    textFormat=Qt.TextFormat.RichText,
                )
            )
        if result.equation:
            equation = QLabel(result.equation, objectName="equation", wordWrap=True)
            equation.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            layout.addWidget(equation)

        # --- details, as label/value rows -------------------------------------------------
        details = list(result.details)
        if added:
            details.append(("Added", join_names(added, most=8)))
        if details:
            grid = QGridLayout()
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(4)
            grid.setColumnStretch(1, 1)
            for row, (label, value) in enumerate(details):
                name = QLabel(label, objectName="detailLabel")
                grid.addWidget(name, row, 0, Qt.AlignmentFlag.AlignTop)
                grid.addWidget(QLabel(value, wordWrap=True), row, 1)
            layout.addLayout(grid)

        # --- breakdowns -------------------------------------------------------------------
        if result.confusion and len(result.confusion[0]) <= self.MAX_LABELS:
            layout.addWidget(
                QLabel("Actual (down) vs. predicted", objectName="cardHeading")
            )
            layout.addLayout(self._confusion_grid(*result.confusion))
        if result.bars:
            layout.addWidget(QLabel(result.bars_title, objectName="cardHeading"))
            layout.addLayout(self._bars(result.bars))
        if result.table is not None:
            layout.addWidget(self._build_table(result))
        if result.plot is not None:
            plot_button = PrimaryButton(result.plot_label, muted=True)
            plot_button.clicked.connect(lambda: self.plot_requested.emit(*result.plot))
            layout.addWidget(plot_button, alignment=Qt.AlignmentFlag.AlignLeft)

    def _confusion_grid(self, labels: list[str], counts: np.ndarray) -> QGridLayout:
        """How many rows of each actual label (down) got each predicted label
        (across). Right answers (the diagonal) are shaded the primary color, and
        wrong ones red."""
        grid = QGridLayout()
        grid.setSpacing(3)
        for i, label in enumerate(labels):
            column_label = _elided(label, self.NAME_WIDTH, "detailLabel")
            column_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(column_label, 0, i + 1)
            grid.addWidget(_elided(label, self.NAME_WIDTH, "detailLabel"), i + 1, 0)
        for i, row in enumerate(counts):
            for j, count in enumerate(row):
                cell = QLabel(f"{count:,}")
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if i == j:
                    background = rgba(theme.PRIMARY_COLOR, 60)
                elif count:
                    background = rgba(theme.ERROR_COLOR, 30)
                else:
                    background = rgba(theme.MUTED_COLOR, 15)
                cell.setStyleSheet(
                    f"background: {background}; border-radius: 4px; padding: 4px;"
                )
                grid.addWidget(cell, i + 1, j + 1)
        for j in range(len(labels)):
            grid.setColumnStretch(j + 1, 1)
        return grid

    def _bars(self, bars: list[tuple[str, float]]) -> QGridLayout:
        """A bar per (name, share of a whole), scaled so the largest is full."""
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(1, 1)
        largest = max(share for _, share in bars) or 1
        for row, (name, share) in enumerate(bars):
            bar = QProgressBar(maximum=1000, textVisible=False)
            bar.setStyleSheet(progress_bar_style())
            bar.setFixedHeight(6)
            bar.setValue(round(1000 * share / largest))
            value = QLabel(f"{share:.0%}", objectName="barValue")
            value.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            grid.addWidget(_elided(name, self.NAME_WIDTH), row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(value, row, 2)
        return grid

    def _build_table(self, result: AnalysisResult) -> QTableWidget:
        table = QTableWidget(result.table.height, result.table.width)
        self.table = table
        table.setHorizontalHeader(SortHeader())
        table.setHorizontalHeaderLabels(result.table.columns)
        table.setStyleSheet(table_style())
        table.setFrameShape(QFrame.Shape.NoFrame)  # the stylesheet draws it
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(self.ROW_HEIGHT)
        header = table.horizontalHeader()
        header.setHighlightSections(False)
        # the first column (e.g. names) fits its values, and the rest share the room
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for row, values in enumerate(result.table.iter_rows()):
            for column, value in enumerate(values):
                item = _ValueItem(value)
                item.setData(ROW_ROLE, row)
                table.setItem(row, column, item)
        # Sortable once filled, so it doesn't sort as it fills. With no column to
        # sort by yet, it keeps the result's order until a header is clicked.
        header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        table.setSortingEnabled(True)
        visible = min(result.table.height, self.VISIBLE_ROWS)
        table.setFixedHeight(header.sizeHint().height() + visible * self.ROW_HEIGHT + 2)

        if result.table_rows is not None:
            table.setMouseTracking(True)  # for cellEntered
            table.setCursor(Qt.CursorShape.PointingHandCursor)
            table.cellEntered.connect(
                lambda row, _: self.rows_hovered.emit(self._rows_at(row))
            )
            table.cellClicked.connect(
                lambda row, _: self.rows_selected.emit(self._rows_at(row))
            )
            # to notice the mouse leaving the table
            table.viewport().installEventFilter(self)
        return table

    def _rows_at(self, row: int) -> set[int]:
        """The dataset rows behind the table's row `row` (as it's sorted now)."""
        return set(self.result.table_rows[self.table.item(row, 0).data(ROW_ROLE)])

    def eventFilter(self, watched, event):
        if (
            self.table is not None
            and watched is self.table.viewport()
            and event.type() == QEvent.Type.Leave
        ):
            self.rows_hovered.emit(set())
        return super().eventFilter(watched, event)


class _ValueItem(QTableWidgetItem):
    """A table cell showing a value rounded for reading, which sorts by the value
    itself (numbers right-aligned, and missing values last)."""

    def __init__(self, value):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            value, text = None, ""
        elif isinstance(value, bool):
            text = str(value)
        elif isinstance(value, int):
            text = f"{value:,}"
        elif isinstance(value, float):
            text = format_number(value)
        else:
            text = str(value)
        super().__init__(text)
        self.value = value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            self.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

    def __lt__(self, other: "QTableWidgetItem") -> bool:
        if self.value is None or other.value is None:
            return other.value is None and self.value is not None
        try:
            return self.value < other.value
        except TypeError:  # values of mixed types
            return str(self.value) < str(other.value)


def _elided(text: str, width: int, object_name: str = "") -> QLabel:
    """A label of `text`, cut short with "…" past `width` px (and then showing all
    of it on hover)."""
    label = QLabel(objectName=object_name)
    elided = label.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, width)
    label.setText(elided)
    if elided != text:
        label.setToolTip(text)
    return label
