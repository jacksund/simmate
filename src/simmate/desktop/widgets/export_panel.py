import html
import time
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.data import ToolkitDataset
from simmate.desktop.data.exports import (
    CRYSTALS,
    EXCEL_MAX_ROWS,
    EXPORT_FORMATS,
    MOLECULES,
    TABLES,
    ExportFormat,
    write_records,
    write_table,
)
from simmate.desktop.data.features import SLOW_FEATURE_ROWS
from simmate.desktop.widgets.background import BackgroundTask, IncrementalTask
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import scroll_bar_style
from simmate.desktop.widgets.confirm_dialog import confirm
from simmate.desktop.widgets.inputs import StyledRadioButton, input_style
from simmate.desktop.widgets.status import callout_style, link, loading_bar, note_label


def export_style() -> str:
    return f"""
#panelTitle {{ color: {theme.MUTED_COLOR}; font-weight: bold; }}
#sectionTitle {{ color: {theme.MUTED_COLOR}; font-weight: 600; }}
#formatTag {{ color: {theme.MUTED_LIGHTER}; font-size: 11px; }}
/* see-through, so the window shows behind the panel like the rest of the app */
#exportScroll, #exportContent {{ background: transparent; }}
{scroll_bar_style()}"""


class ExportPanel(QWidget):
    """The dashboard's Export column: saves every row and column of the dataset
    (including any added since it was opened) to a file, as one of `EXPORT_FORMATS`.

    Table formats (CSV, Excel, and Parquet) are always offered, molecule formats
    (SDF, SMILES, and XYZ) when the dataset has a column of SMILES, and crystal
    formats (CIF and POSCAR) when it has a column of structures. Formats written a
    record at a time show their progress and can be cancelled; those tagged "slow"
    ask first on datasets of more than `SLOW_FEATURE_ROWS` rows.

    The file is written as `<name>.part` first, then renamed once done, so a
    stopped or failed export never looks finished.
    """

    folder = Path.home()  # where the save dialog opens: the last folder used

    def __init__(self, dataset: ToolkitDataset):
        super().__init__()
        self.dataset = dataset
        self.task: BackgroundTask | IncrementalTask | None = None
        self.steps = None  # the running `write_records`, if any
        self.fmt: ExportFormat | None = None  # of the running (or last) export
        self.path: Path | None = None  # where it's saved
        self.skipped: list[int] = []  # rows it left out
        self.started = 0.0  # when it began (perf_counter)
        self.setStyleSheet(export_style() + input_style())

        title = QLabel("Export", objectName="panelTitle")
        font = title.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        title.setFont(font)
        about = note_label(
            f"Saves all {dataset.height:,} rows and every column, including any "
            "you've added."
        )

        # --- the formats, one heading per section ---------------------------------------
        content = QWidget(objectName="exportContent")
        content_layout = QVBoxLayout(content)
        # breathing room from the window's edges and the pull tab's line (right)
        content_layout.setContentsMargins(8, 0, 12, 8)
        content_layout.setSpacing(8)
        sections = {TABLES}
        if dataset.has_molecules:
            sections.add(MOLECULES)
        if dataset.has_structures:
            sections.add(CRYSTALS)
        self.group = QButtonGroup(self)
        self.choices: list[tuple[ExportFormat, StyledRadioButton]] = []
        section = None
        for fmt in EXPORT_FORMATS:
            if fmt.section not in sections:
                continue
            if fmt.section != section:
                if section is not None:
                    content_layout.addSpacing(12)
                content_layout.addWidget(QLabel(fmt.section, objectName="sectionTitle"))
                section = fmt.section
            radio = StyledRadioButton(fmt.name)
            radio.setToolTip(fmt.description)
            if fmt.key == "xlsx" and dataset.height > EXCEL_MAX_ROWS:
                radio.setEnabled(False)
                radio.setToolTip(
                    f"An Excel sheet holds at most {EXCEL_MAX_ROWS:,} rows, and this "
                    f"dataset has {dataset.height:,}"
                )
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(radio, stretch=1)
            if fmt.slow:
                slow_tag = QLabel("slow", objectName="formatTag")
                slow_tag.setToolTip(
                    f"Gets slow past {SLOW_FEATURE_ROWS:,} rows, as each row takes a "
                    "while"
                )
                row.addWidget(slow_tag)
            row.addWidget(QLabel(fmt.suffix, objectName="formatTag"))
            content_layout.addLayout(row)
            self.group.addButton(radio)
            self.choices.append((fmt, radio))
        self.choices[0][1].setChecked(True)
        content_layout.addStretch()

        scroll = QScrollArea(objectName="exportScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        scroll.viewport().setAutoFillBackground(False)

        # --- footer: stays below the list ---------------------------------------------
        # busy while a table is written; given a maximum for a run of records
        self.progress_bar = loading_bar()
        self.note = note_label("")  # while an export is going
        self.note.hide()
        # how the last export went: a primary-colored (done) or red (failed) callout
        self.result = QLabel(wordWrap=True, textFormat=Qt.TextFormat.RichText)
        self.result.setOpenExternalLinks(True)  # file:// opens the file explorer
        self.result.hide()
        self.export_button = PrimaryButton("Export…", filled=True)
        self.export_button.clicked.connect(self.export)
        self.cancel_button = PrimaryButton("Cancel", muted=True)
        self.cancel_button.clicked.connect(self.cancel)
        self.cancel_button.hide()
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self.export_button, stretch=1)
        buttons.addWidget(self.cancel_button)

        header = QVBoxLayout()
        header.setContentsMargins(8, 8, 12, 8)
        header.setSpacing(12)
        header.addWidget(title)
        header.addWidget(about)
        footer = QVBoxLayout()
        footer.setContentsMargins(8, 8, 12, 8)
        footer.setSpacing(8)
        footer.addWidget(self.progress_bar)
        footer.addWidget(self.note)
        footer.addWidget(self.result)
        footer.addLayout(buttons)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header)
        layout.addWidget(scroll, stretch=1)
        layout.addLayout(footer)

    @property
    def part(self) -> Path:
        """Where the export is written until it's done."""
        return self.path.with_name(f"{self.path.name}.part")

    def export(self):
        """Ask where to save the chosen format, then write it in the background."""
        fmt = next(fmt for fmt, radio in self.choices if radio.isChecked())
        if (
            fmt.slow
            and self.dataset.height > SLOW_FEATURE_ROWS
            and not confirm(
                self,
                "Export a large dataset?",
                f"{fmt.name} doesn't scale well. This dataset has "
                f"{self.dataset.height:,} rows, more than {SLOW_FEATURE_ROWS:,}, so "
                "it may take a long time.",
                yes="Export anyway",
                no="Cancel",
            )
        ):
            return
        # zips of single files are named for what's in them, e.g. "name-cif.zip"
        stem = self.dataset.name
        if fmt.suffix == ".zip":
            stem += f"-{fmt.key}"
        file, _ = QFileDialog.getSaveFileName(
            self,
            f"Export as {fmt.name}",
            str(ExportPanel.folder / f"{stem}{fmt.suffix}"),
            f"{fmt.name} (*{fmt.suffix})",
        )
        if not file:
            return
        path = Path(file)
        if path.suffix.lower() != fmt.suffix:
            path = path.with_name(path.name + fmt.suffix)
        ExportPanel.folder = path.parent
        self.fmt, self.path, self.skipped = fmt, path, []

        if fmt.per_row:
            self.steps = write_records(self.dataset, fmt, self.part, self.skipped)
            self.task = IncrementalTask(self.steps, self.dataset.height, self)
            self.task.progress.connect(self._on_progress)
            self.progress_bar.setMaximum(max(self.dataset.height, 1))
            self.progress_bar.setValue(0)
        else:
            dataset, part = self.dataset, self.part
            # Not parented to the panel, which is deleted if the dataset is closed
            # mid-run. Its connections to the panel's methods go with the panel.
            self.task = BackgroundTask(lambda _: write_table(dataset, fmt, part))
            self.progress_bar.setMaximum(0)  # busy
        self.task.finished.connect(self._on_finished)
        self.task.failed.connect(self._on_failed)
        self.note.setText(f"Exporting {_rows(self.dataset.height)}…")
        self._set_running(True)
        self.started = time.perf_counter()
        self.task.start()

    def cancel(self):
        """Stop the running export, deleting what it had written."""
        if self.steps is None:
            return
        self.task.cancel()
        self.steps.close()  # closes its file
        self.task = self.steps = None
        self.part.unlink(missing_ok=True)
        self._set_running(False)

    def _on_progress(self, done: int, total: int):
        self.progress_bar.setValue(done)
        self.note.setText(f"Exporting {done:,} of {_rows(total)}…")

    def _on_finished(self, *_):
        self.task = self.steps = None
        self.part.replace(self.path)
        self._set_running(False)

        written = self.dataset.height - len(self.skipped)
        lines = [f"<b>✓ Exported {_rows(written)} to {html.escape(self.path.name)}</b>"]
        if self.skipped:
            reason = "read or made 3D" if self.fmt.key == "xyz" else "read"
            lines.append(
                f"Left out {_rows(len(self.skipped))}, as their structures couldn't "
                f"be {reason}"
            )
        elapsed = time.perf_counter() - self.started
        took = (
            f"{elapsed:.1f}s"
            if elapsed < 60
            else f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
        )
        folder_url = QUrl.fromLocalFile(str(self.path.parent)).toString()
        lines.append(
            f"Done in {took} &nbsp;·&nbsp; {link(folder_url, 'Show in folder')}"
        )
        self.result.setStyleSheet(callout_style(theme.PRIMARY_COLOR))
        self.result.setText("<br>".join(lines))
        self.result.show()

    def _on_failed(self, error: str):
        self.task = self.steps = None
        self.part.unlink(missing_ok=True)
        self._set_running(False)
        self.result.setStyleSheet(callout_style(theme.ERROR_COLOR))
        self.result.setText(f"<b>✗ Couldn't export</b><br>{html.escape(error)}")
        self.result.show()

    def _set_running(self, running: bool):
        self.progress_bar.setVisible(running)
        self.note.setVisible(running)
        self.cancel_button.setVisible(running and self.steps is not None)
        self.export_button.setEnabled(not running)
        if running:
            self.result.hide()


def _rows(count: int) -> str:
    return f"{count:,} row" + ("" if count == 1 else "s")
