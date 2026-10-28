import html
import time

import polars
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.data import ToolkitDataset
from simmate.desktop.data.features import (
    CLUSTERS,
    DIMS,
    FEATURES,
    SLOW_FEATURE_ROWS,
    Feature,
    compute_features,
)
from simmate.desktop.widgets.background import BackgroundTask
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import scroll_bar_style
from simmate.desktop.widgets.confirm_dialog import confirm
from simmate.desktop.widgets.inputs import StyledCheckBox, StyledComboBox, input_style
from simmate.desktop.widgets.status import callout_style, loading_bar, note_label


def featurize_style() -> str:
    return f"""
#panelTitle {{ color: {theme.MUTED_COLOR}; font-weight: bold; }}
#sectionTitle {{ color: {theme.MUTED_COLOR}; font-weight: 600; }}
#featureTag {{ color: {theme.MUTED_LIGHTER}; font-size: 11px; }}
#presentTag {{ color: {theme.PRIMARY_COLOR}; font-size: 11px; font-weight: 600; }}
/* see-through, so the window shows behind the panel like the rest of the app */
#featurizeScroll, #featurizeContent {{ background: transparent; }}
{scroll_bar_style()}"""


class FeaturizePanel(QWidget):
    """The dashboard's Featurize column: a checklist of columns that
    `simmate.toolkit` can add to the dataset (see `FEATURES`), such as molecular
    properties, identifiers, SMARTS-set matches, fingerprints, chemical-space maps
    and clusters.

    Tick any number, then "Add N columns" computes them all in the background (in
    parallel wherever the toolkit offers it). Options that don't scale well (tagged
    "slow") ask first on datasets of more than `SLOW_FEATURE_ROWS` rows. An option
    whose columns are already in the dataset is tagged "in dataset" and disabled,
    unless it has a setting (e.g. 2D or 3D) to re-run it with, which replaces its
    columns.

    `columns_added(added, replaced)` fires with the column names once they're in the
    dataset (see `ToolkitDataset.add_columns`).
    """

    columns_added = Signal(object, object)

    MAX_NAMES = 6  # columns named in the "Added" message

    def __init__(self, dataset: ToolkitDataset):
        super().__init__()
        self.dataset = dataset
        self.task: BackgroundTask | None = None
        self.started = 0.0  # when the run began (perf_counter)
        self.rows: list[_FeatureRow] = []
        self.setStyleSheet(featurize_style() + input_style())

        title = QLabel("Featurize", objectName="panelTitle")
        font = title.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        title.setFont(font)
        self.search = QLineEdit(placeholderText="Find a feature…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._show_matching_rows)

        # --- the checklist, one heading per section -----------------------------------
        content = QWidget(objectName="featurizeContent")
        content_layout = QVBoxLayout(content)
        # breathing room from the window's edges and the pull tab's line (right)
        content_layout.setContentsMargins(8, 0, 12, 8)
        content_layout.setSpacing(8)
        # section -> its heading, hidden while a search matches none of its rows
        self.headings: dict[str, QLabel] = {}
        if dataset.has_molecules:
            for feature in FEATURES:
                if feature.section not in self.headings:
                    heading = QLabel(feature.section, objectName="sectionTitle")
                    if self.headings:
                        content_layout.addSpacing(12)
                    content_layout.addWidget(heading)
                    self.headings[feature.section] = heading
                row = _FeatureRow(feature)
                row.changed.connect(self._update_button)
                # a new setting (e.g. 3D) may need columns the dataset lacks
                row.changed.connect(self._mark_present)
                content_layout.addWidget(row)
                self.rows.append(row)
        else:
            self.search.hide()
            content_layout.addWidget(
                note_label("Featurizing needs a column of molecules (as SMILES).")
            )
        content_layout.addStretch()

        scroll = QScrollArea(objectName="featurizeScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        scroll.viewport().setAutoFillBackground(False)

        # --- footer: stays below the list ---------------------------------------------
        self.loading_bar = loading_bar()
        self.note = note_label("")  # while a run is going
        self.note.hide()
        # how the last run went: a primary-colored (done) or red (failed) callout
        self.result = QLabel(wordWrap=True, textFormat=Qt.TextFormat.RichText)
        self.result.hide()
        self.add_button = PrimaryButton("Add columns", filled=True)
        self.add_button.clicked.connect(self.add_chosen)

        header = QVBoxLayout()
        header.setContentsMargins(8, 8, 12, 8)
        header.setSpacing(12)
        header.addWidget(title)
        header.addWidget(self.search)
        footer = QVBoxLayout()
        footer.setContentsMargins(8, 8, 12, 8)
        footer.setSpacing(8)
        footer.addWidget(self.loading_bar)
        footer.addWidget(self.note)
        footer.addWidget(self.result)
        footer.addWidget(self.add_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header)
        layout.addWidget(scroll, stretch=1)
        layout.addLayout(footer)
        self.add_button.setVisible(dataset.has_molecules)

        self._mark_present()
        self._update_button()

    def add_chosen(self):
        """Compute the ticked options' columns in the background, then add them."""
        rows = [row for row in self.rows if row.checkbox.isChecked()]
        slow = [row.feature.name for row in rows if row.feature.slow]
        if (
            slow
            and self.dataset.height > SLOW_FEATURE_ROWS
            and not confirm(
                self,
                "Run on a large dataset?",
                f"Some of these don't scale well ({', '.join(slow)}). This dataset "
                f"has {self.dataset.height:,} rows, more than {SLOW_FEATURE_ROWS:,}, "
                "so they may take a long time and use a lot of memory.",
                yes="Run anyway",
                no="Cancel",
            )
        ):
            return

        chosen = [(row.feature, row.setting()) for row in rows]
        smiles = self.dataset.df[self.dataset.molecule_column].to_list()
        # Not parented to the panel, which is deleted if the dataset is closed
        # mid-run. Its connections to the panel's methods go with the panel, so the
        # result is then dropped.
        self.task = BackgroundTask(lambda _: compute_features(smiles, chosen))
        self.task.finished.connect(self._on_finished)
        self.task.failed.connect(self._on_failed)
        message = f"Adding {_count(sum(len(row.columns()) for row in rows))}…"
        self.note.setText(message)
        self.note.show()
        self.result.hide()
        self.loading_bar.show()
        self._update_button()
        self.started = time.perf_counter()
        self.task.start()

    def _on_finished(self, new: polars.DataFrame):
        self.task = None
        added, replaced = self.dataset.add_columns(new)
        for row in self.rows:
            row.checkbox.setChecked(False)
        self._mark_present()
        self.loading_bar.hide()
        self.note.hide()
        self._update_button()
        self.columns_added.emit(added, replaced)

        # e.g. "Added 1 column, replaced 2 columns"
        parts = []
        if added:
            parts.append(f"added {_count(len(added))}")
        if replaced:
            parts.append(f"replaced {_count(len(replaced))}")
        message = ", ".join(parts).capitalize()
        names = ", ".join(new.columns[: self.MAX_NAMES])
        if len(new.columns) > self.MAX_NAMES:
            names += f" and {len(new.columns) - self.MAX_NAMES} more"
        elapsed = time.perf_counter() - self.started
        took = (
            f"{elapsed:.1f}s"
            if elapsed < 60
            else f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        )
        self.result.setStyleSheet(callout_style(theme.PRIMARY_COLOR))
        self.result.setText(f"<b>✓ {message}</b><br>{names}<br>Done in {took}")
        self.result.show()

    def _on_failed(self, error: str):
        self.task = None
        self.loading_bar.hide()
        self.note.hide()
        self.result.setStyleSheet(callout_style(theme.ERROR_COLOR))
        self.result.setText(
            f"<b>✗ Couldn't add the columns</b><br>{html.escape(error)}"
        )
        self.result.show()
        self._update_button()

    def _mark_present(self):
        """Tag the options whose columns are all in the dataset already."""
        present = set(self.dataset.df.columns)
        for row in self.rows:
            row.set_present(set(row.columns()) <= present)

    def _update_button(self):
        count = sum(len(row.columns()) for row in self.rows if row.checkbox.isChecked())
        self.add_button.setText(f"Add {_count(count)}" if count else "Add columns")
        self.add_button.setEnabled(bool(count) and self.task is None)

    def _show_matching_rows(self, text: str):
        text = text.lower()
        for row in self.rows:
            row.setVisible(
                text in row.feature.name.lower()
                or any(text in column for column in row.columns())
            )
        for section, heading in self.headings.items():
            heading.setVisible(
                any(
                    not row.isHidden()
                    for row in self.rows
                    if row.feature.section == section
                )
            )


class _FeatureRow(QWidget):
    """One option of the checklist: its checkbox, then its tags and setting (if any).

    `changed` fires when it's ticked or its setting changes."""

    changed = Signal()

    def __init__(self, feature: Feature):
        super().__init__()
        self.feature = feature
        self.checkbox = StyledCheckBox(feature.name)
        self.checkbox.toggled.connect(self.changed)
        self.present_tag = QLabel("✓ in dataset", objectName="presentTag")
        self.present_tag.setToolTip(
            "Already in the dataset. Adding it again replaces these columns."
            if feature.setting
            else "Already in the dataset"
        )
        self.present_tag.hide()

        self.setting_input = None
        if feature.setting == DIMS:
            self.setting_input = StyledComboBox()
            self.setting_input.addItems(["2D", "3D"])
            self.setting_input.currentIndexChanged.connect(self._on_setting_changed)
        elif feature.setting == CLUSTERS:
            self.setting_input = QSpinBox(minimum=2, maximum=1000, value=10)
            self.setting_input.setSuffix(" clusters")
            self.setting_input.setToolTip("How many clusters to make")
            self.setting_input.valueChanged.connect(self._on_setting_changed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.checkbox, stretch=1)
        layout.addWidget(self.present_tag)
        if feature.slow:
            slow_tag = QLabel("slow", objectName="featureTag")
            slow_tag.setToolTip(
                f"Gets slow past {SLOW_FEATURE_ROWS:,} rows, as it doesn't scale well"
            )
            layout.addWidget(slow_tag)
        if self.setting_input is not None:
            layout.addWidget(self.setting_input)
        self._update_tooltip()

    def setting(self) -> int | None:
        """The chosen setting: the number of dimensions or clusters, if it has one."""
        if self.feature.setting == DIMS:
            return self.setting_input.currentIndex() + 2  # "2D" is first
        if self.feature.setting == CLUSTERS:
            return self.setting_input.value()
        return None

    def columns(self) -> list[str]:
        """The columns it adds with its current setting."""
        return self.feature.columns(self.setting())

    def set_present(self, present: bool):
        """Show whether its columns are all in the dataset already. If so, it's
        disabled, unless it has a setting to re-run it with (e.g. 3D after 2D, or
        another number of clusters)."""
        self.present_tag.setVisible(present)
        self.checkbox.setEnabled(not present or self.feature.setting is not None)

    def _on_setting_changed(self, *_):
        self._update_tooltip()
        self.changed.emit()

    def _update_tooltip(self):
        about = f"{self.feature.description}\n\n" if self.feature.description else ""
        self.checkbox.setToolTip(f"{about}Adds: {', '.join(self.columns())}")


def _count(columns: int) -> str:
    return f"{columns} column" + ("" if columns == 1 else "s")
