from pathlib import Path

import requests
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.widgets.background import BackgroundTask
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import table_style
from simmate.desktop.widgets.dataset_browser import get_datasets_dir
from simmate.desktop.widgets.plot_toolbar import download_icon
from simmate.desktop.widgets.status import (
    heading_label,
    note_label,
    progress_bar_style,
    set_status,
)

ASSETS_URL = "https://assets.simmate.org"

CATALOGS = [
    # (group, name, rows, size, url), as on the website's Data Explorer > Downloads
    (
        "Crystalline",
        "AFLOW Prototypes",
        "288",
        "75 KB",
        f"{ASSETS_URL}/aflow/archive/AflowPrototype-full-2026-08-17.parquet",
    ),
    (
        "Crystalline",
        "Crystallography Open Database (COD)",
        "~522,000",
        "1 GB",
        f"{ASSETS_URL}/cod/archive/CodStructure-full-2026-08-17.parquet",
    ),
    (
        "Crystalline",
        "JARVIS",
        "~76,000",
        "30 MB",
        f"{ASSETS_URL}/jarvis/archive/JarvisStructure-full-2026-08-17.parquet",
    ),
    (
        "Crystalline",
        "Materials Project",
        "~200,000",
        "120 MB",
        f"{ASSETS_URL}/materials_project/archive/MatprojStructure-full-2026-08-17.parquet",
    ),
    (
        "Crystalline",
        "Open Quantum Materials Database (OQMD)",
        "~1,200,000",
        "400 MB",
        f"{ASSETS_URL}/oqmd/archive/OqmdStructure-full-2026-08-17.parquet",
    ),
    (
        "Molecular",
        "ChEMBL",
        "~2,900,000",
        "250 MB",
        f"{ASSETS_URL}/chembl/archive/ChemblMolecule-full-2026-08-17.parquet",
    ),
]
"""
The ready-made datasets offered for download: snapshots of popular catalogs,
hosted by Simmate.
"""

CHUNK_SIZE = 1 << 20  # 1 MB


def download_file(url: str, target: Path, task: BackgroundTask) -> Path | None:
    """
    Downloads `url` to `target`, reporting progress in bytes through `task`.
    It goes to a `.part` file first, so a stopped download never looks finished.
    Returns None (and removes the partial file) if the task is cancelled.
    """
    part = target.with_name(f"{target.name}.part")
    try:
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", 0))
            done = 0
            with part.open("wb") as file:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if task.cancelled:
                        break
                    file.write(chunk)
                    done += len(chunk)
                    task.progress.emit(done, total)
    except Exception:
        part.unlink(missing_ok=True)
        raise
    if task.cancelled:
        part.unlink(missing_ok=True)
        return None
    part.rename(target)
    return target


def _megabytes(size: int) -> str:
    return f"{size / 1e6:,.0f} MB"


class DatasetDownloads(QWidget):
    """
    The ready-made `CATALOGS`, each downloadable into the datasets folder.
    `downloaded` fires with the new file once one finishes.
    """

    downloaded = Signal(Path)
    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.tasks: dict[str, BackgroundTask] = {}  # running downloads, by url

        about = note_label(
            "Snapshots of popular third-party catalogs, saved to your datasets as "
            "parquet files. Simmate isn't affiliated with these catalogs, so please "
            "cite their original sources when you use the data."
        )
        self.message = QLabel()
        self.message.hide()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Dataset", "Rows", "Size", ""])
        self.table.setStyleSheet(table_style())
        self.table.setFrameShape(QFrame.Shape.NoFrame)  # the stylesheet draws it
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(36)
        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 230)  # fits the progress bar and Cancel
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._fill_table()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(heading_label("Download"))
        layout.addWidget(about)
        layout.addWidget(self.message)
        layout.addWidget(self.table, stretch=1)

    def _fill_table(self):
        self.rows: dict[str, int] = {}  # the table row of each url
        group = None
        for catalog_group, name, rows, size, url in CATALOGS:
            if catalog_group != group:  # a heading row, across the whole table
                group = catalog_group
                row = self.table.rowCount()
                self.table.insertRow(row)
                heading = QTableWidgetItem(group)
                font = QFont(heading.font())
                font.setBold(True)
                heading.setFont(font)
                heading.setForeground(Qt.GlobalColor.gray)
                self.table.setItem(row, 0, heading)
                self.table.setSpan(row, 0, 1, 4)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, text in enumerate([name, rows, size]):
                self.table.setItem(row, column, QTableWidgetItem(text))
            self.rows[url] = row
        self.refresh()

    def refresh(self):
        """Updates each row's button, e.g. after a dataset was moved or deleted."""
        saved = {path.name for path in get_datasets_dir().rglob("*.parquet")}
        for url, row in self.rows.items():
            if url not in self.tasks:
                self.table.setCellWidget(row, 3, self._button(url, saved))

    def _button(self, url: str, saved: set[str]) -> QWidget:
        filename = url.rsplit("/", 1)[-1]
        if filename in saved:
            button = PrimaryButton("Downloaded", muted=True)
            button.setEnabled(False)
        else:
            button = PrimaryButton(
                "Download", icon=download_icon(color=theme.PRIMARY_COLOR)
            )
            button.clicked.connect(lambda: self.download(url))
        return _cell(button)

    def download(self, url: str):
        target = get_datasets_dir() / url.rsplit("/", 1)[-1]
        task = BackgroundTask(lambda task: download_file(url, target, task), self)
        self.tasks[url] = task

        bar = QProgressBar(maximum=0, textVisible=False)  # busy until the size is known
        bar.setStyleSheet(progress_bar_style())
        bar.setFixedHeight(8)
        amount = note_label("Starting…")
        amount.setWordWrap(False)
        cancel = PrimaryButton("Cancel", muted=True)
        cancel.clicked.connect(task.cancel)
        progress = QVBoxLayout()
        progress.setSpacing(2)
        progress.addStretch()
        progress.addWidget(bar)
        progress.addWidget(amount)
        progress.addStretch()
        cell = QWidget()
        layout = QHBoxLayout(cell)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.addLayout(progress, stretch=1)
        layout.addWidget(cancel)
        self.table.setCellWidget(self.rows[url], 3, cell)

        def on_progress(done: int, total: int):
            if total:
                bar.setMaximum(1000)
                bar.setValue(int(1000 * done / total))
                amount.setText(f"{_megabytes(done)} of {_megabytes(total)}")
            else:
                amount.setText(_megabytes(done))

        task.progress.connect(on_progress)
        task.finished.connect(lambda path: self._finished(url, path))
        task.failed.connect(lambda error: self._failed(url, error))
        self.message.hide()
        self.status.emit(f"Downloading {target.name}…")
        task.start()

    def _finished(self, url: str, path: Path | None):
        del self.tasks[url]
        self.refresh()
        if path is None:
            self.status.emit("Download cancelled")
            return
        self.status.emit(f"Downloaded {path.name}")
        self.downloaded.emit(path)

    def _failed(self, url: str, error: str):
        del self.tasks[url]
        self.refresh()
        set_status(self.message, f"Download failed: {error}", False)
        self.message.show()
        self.status.emit("Download failed")


def _cell(widget: QWidget) -> QWidget:
    """`widget`, padded to sit in a table cell."""
    cell = QWidget()
    layout = QHBoxLayout(cell)
    layout.setContentsMargins(8, 0, 8, 0)
    layout.addWidget(widget)
    return cell
