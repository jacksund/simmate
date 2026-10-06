import shutil
from pathlib import Path

import polars
from PySide6.QtCore import QDir, QFileInfo, QModelIndex, Qt, QUrl, Signal
from PySide6.QtGui import QAbstractFileIconProvider, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFileSystemModel,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from simmate.config import settings
from simmate.desktop import theme
from simmate.desktop.widgets.background import BackgroundTask
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import table_style
from simmate.desktop.widgets.plot_toolbar import (
    folder_icon,
    plus_icon,
    trash_icon,
)
from simmate.desktop.widgets.status import (
    heading_label,
    link,
    loading_bar,
    note_label,
    set_status,
)

DATASET_SUFFIX = ".parquet"
UPLOAD_FILTER = "Datasets (*.sdf *.csv *.parquet)"


def get_datasets_dir() -> Path:
    """
    Where the desktop app keeps datasets (`~/simmate/desktop/datasets` by default).
    Each dataset is one table, saved as a parquet file, and may sit in subfolders.
    """
    directory = settings.config_directory / "desktop" / "datasets"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def unique_path(path: Path) -> Path:
    """`path`, or `name (2).ext`, `name (3).ext`, ... if it's already taken."""
    candidate, number = path, 2
    while candidate.exists():
        candidate = path.with_name(f"{path.stem} ({number}){path.suffix}")
        number += 1
    return candidate


def import_dataset(source: Path, folder: Path) -> Path:
    """
    Saves a copy of `source` (a .parquet, .csv or .sdf file) in `folder` as parquet,
    and returns the new file. SDF records become rows of SMILES plus their properties.
    """
    source = Path(source)
    target = unique_path(folder / f"{source.stem}{DATASET_SUFFIX}")
    suffix = source.suffix.lower()
    if suffix == ".parquet":
        shutil.copyfile(source, target)
    elif suffix == ".csv":
        polars.read_csv(source, infer_schema_length=10_000).write_parquet(target)
    elif suffix == ".sdf":
        _read_sdf(source).write_parquet(target)
    else:
        raise ValueError(f"Can't import {source.name}: use .sdf, .csv or .parquet")
    return target


def _read_sdf(source: Path) -> polars.DataFrame:
    """An SDF file as a table: one row per molecule, of its SMILES and properties."""
    from simmate.toolkit import Molecule

    molecules = Molecule.from_sdf_file(source, skip_failed=True)
    if not isinstance(molecules, list):
        molecules = [molecules]
    rows = [
        {
            "smiles": molecule.to_smiles(),
            # as text, then typed per column below (rdkit guesses per molecule)
            **{
                key: str(value)
                for key, value in molecule.metadata.items()
                if not key.startswith("_")  # rdkit's private props, e.g. _Name
            },
        }
        for molecule in molecules
    ]
    df = polars.from_dicts(rows, infer_schema_length=None)
    return df.with_columns(
        _parse_numbers(df[column]) for column in df.columns if column != "smiles"
    )


def _parse_numbers(column: polars.Series) -> polars.Series:
    """`column` as integers or floats if every value is one, else unchanged."""
    for dtype in (polars.Int64, polars.Float64):
        try:
            return column.cast(dtype)
        except polars.exceptions.InvalidOperationError:
            continue
    return column


class FolderIcons(QAbstractFileIconProvider):
    """A folder icon for folders, and none for datasets (rather than the OS's)."""

    def __init__(self):
        super().__init__()
        # only the "off" look: the tree draws open folders with the "on" one,
        # which our button icons have in white (for checked buttons)
        self.folder = _off_only(folder_icon(color=theme.PRIMARY_COLOR))

    def icon(self, info):
        if isinstance(info, QFileInfo):
            return self.folder if info.isDir() else QIcon()
        return self.folder if info == self.IconType.Folder else QIcon()


class DatasetFileModel(QFileSystemModel):
    """
    The datasets folder: subfolders and parquet files. Files show (and are renamed)
    without their extension, which the Type column shows instead.
    """

    TYPE_COLUMN = 2

    def __init__(self, root: Path):
        super().__init__()
        self.setReadOnly(False)  # renames and drag-and-drop moves
        self.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )
        self.setNameFilters([f"*{DATASET_SUFFIX}"])
        self.setNameFilterDisables(False)  # hide other files, rather than grey them
        self.icons = FolderIcons()  # kept, as the model doesn't own it
        self.setIconProvider(self.icons)
        self.setRootPath(str(root))

    def _is_dataset(self, index: QModelIndex) -> bool:
        return index.column() == 0 and not self.isDir(index)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.column() == self.TYPE_COLUMN and role == Qt.ItemDataRole.DisplayRole:
            # the extension, rather than the OS's description (e.g. "parquet File")
            return "Folder" if self.isDir(index) else self.fileInfo(index).suffix()
        value = super().data(index, role)
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if self._is_dataset(index) and value.endswith(DATASET_SUFFIX):
                return value.removesuffix(DATASET_SUFFIX)
        return value

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not self._is_dataset(index) or role != Qt.ItemDataRole.EditRole:
            return super().setData(index, value, role)
        # Renamed here: Qt's own rename reads the old name back through `data`,
        # which leaves off the extension, so it can't find the file.
        name = value.strip().removesuffix(DATASET_SUFFIX)
        if not name or "/" in name or "\\" in name:
            return False
        path = Path(self.filePath(index))
        target = path.with_name(name + DATASET_SUFFIX)
        if target == path:
            return True
        if target.exists():
            return False
        path.rename(target)  # the model sees the change and updates itself
        return True


class DatasetBrowser(QWidget):
    """
    The datasets saved on this computer (see `get_datasets_dir`), where datasets can
    be uploaded, renamed, deleted and organized into folders (drag to move).

    `status` reports what it did, for the window's status bar.
    """

    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.root = get_datasets_dir()
        self.model = DatasetFileModel(self.root)

        upload_button = PrimaryButton(
            "Upload", icon=plus_icon(color=theme.PRIMARY_COLOR)
        )
        upload_button.setToolTip(
            "Add your own .sdf, .csv or .parquet files, saved here as parquet"
        )
        upload_button.clicked.connect(self.upload)
        folder_button = PrimaryButton("New folder", muted=True, icon=folder_icon())
        folder_button.clicked.connect(self.new_folder)
        self.rename_button = PrimaryButton("Rename", muted=True)
        self.rename_button.clicked.connect(self.rename)
        self.delete_button = PrimaryButton("Delete", muted=True, icon=trash_icon())
        self.delete_button.clicked.connect(self.delete)
        # TODO: load the selected dataset into the Toolkit tab
        self.open_button = PrimaryButton("Open in Toolkit", filled=True)
        self.open_button.setToolTip("Coming soon")
        buttons = QHBoxLayout()
        buttons.addWidget(upload_button)
        buttons.addWidget(folder_button)
        buttons.addWidget(self.rename_button)
        buttons.addWidget(self.delete_button)
        buttons.addStretch()
        buttons.addWidget(self.open_button)

        self.loading_bar = loading_bar()
        self.message = QLabel()
        self.message.hide()

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(self.root)))
        # taller rows than the default, nearer the tables' 40px
        self.tree.setStyleSheet(table_style() + "QTreeView::item { min-height: 30px; }")
        self.tree.setFrameShape(QFrame.Shape.NoFrame)  # the stylesheet draws it
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        header = self.tree.header()
        header.setHighlightSections(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3):  # size, type and date modified
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setEditTriggers(
            QAbstractItemView.EditTrigger.EditKeyPressed  # F2
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        # drag files and folders onto folders to move them
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.tree.selectionModel().selectionChanged.connect(self._update_buttons)

        folder_url = QUrl.fromLocalFile(str(self.root)).toString()
        location = note_label(
            f"Saved in {_display_path(self.root)} &nbsp;·&nbsp; "
            f"{link(folder_url, 'Open folder')}"
        )
        location.setOpenExternalLinks(True)  # file:// opens the file explorer

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(heading_label("My datasets"))
        layout.addLayout(buttons)
        layout.addWidget(self.loading_bar)
        layout.addWidget(self.message)
        layout.addWidget(self.tree)
        layout.addWidget(location)
        self._update_buttons()

    def _selected(self) -> QModelIndex | None:
        indexes = self.tree.selectionModel().selectedRows()
        return indexes[0] if indexes else None

    def _target_folder(self) -> Path:
        """The selected folder (or the selected file's), where new items go."""
        index = self._selected()
        if index is None:
            return self.root
        path = Path(self.model.filePath(index))
        return path if self.model.isDir(index) else path.parent

    def _update_buttons(self):
        selected = self._selected() is not None
        self.rename_button.setEnabled(selected)
        self.delete_button.setEnabled(selected)
        self.open_button.setEnabled(False)  # TODO: selected and not a folder

    def select(self, path: Path):
        """Selects (and scrolls to) a file or folder in the datasets folder."""
        index = self.model.index(str(path))
        if index.isValid():
            self.tree.setCurrentIndex(index)
            self.tree.scrollTo(index)

    def upload(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Upload datasets", str(Path.home()), UPLOAD_FILTER
        )
        if not files:
            return
        folder = self._target_folder()
        task = BackgroundTask(
            lambda _: [import_dataset(Path(file), folder) for file in files], self
        )
        task.finished.connect(self._uploaded)
        task.failed.connect(self._upload_failed)
        self.loading_bar.show()
        self.message.hide()
        self.status.emit(f"Converting {len(files)} file(s) to parquet…")
        task.start()

    def _uploaded(self, paths: list[Path]):
        self.loading_bar.hide()
        self.status.emit(f"Added {', '.join(path.stem for path in paths)}")
        self.select(paths[-1])

    def _upload_failed(self, error: str):
        self.loading_bar.hide()
        set_status(self.message, f"Upload failed: {error}", False)
        self.message.show()
        self.status.emit("Upload failed")

    def new_folder(self):
        folder = self._target_folder()
        index = self.model.mkdir(
            self.model.index(str(folder)), unique_path(folder / "New folder").name
        )
        if index.isValid():
            self.tree.setCurrentIndex(index)
            self.tree.edit(index)  # name it right away

    def rename(self):
        index = self._selected()
        if index is not None:
            self.tree.edit(index.siblingAtColumn(0))

    def delete(self):
        index = self._selected()
        if index is None:
            return
        name = self.model.data(index.siblingAtColumn(0))
        what = (
            f"the folder '{name}' and everything in it"
            if self.model.isDir(index)
            else f"'{name}'"
        )
        answer = QMessageBox.question(
            self, "Delete", f"Delete {what}? This can't be undone."
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if self.model.remove(index):  # folders are removed with their contents
            self.status.emit(f"Deleted {name}")
        else:
            set_status(self.message, f"Couldn't delete {name}.", False)
            self.message.show()


def _off_only(icon: QIcon, size: int = 16) -> QIcon:
    """`icon`, the same in every state."""
    return QIcon(icon.pixmap(size, QIcon.Mode.Normal, QIcon.State.Off))


def _display_path(path: Path) -> str:
    """`path`, with the home folder shortened to `~`."""
    try:
        return str(Path("~") / path.relative_to(Path.home()))
    except ValueError:
        return str(path)
