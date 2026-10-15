from PySide6.QtCore import QByteArray, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.data import CATEGORY, ToolkitDataset
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import format_value
from simmate.desktop.widgets.molecule_3d import Molecule3DView
from simmate.toolkit import Molecule

MAX_TEXT = 200  # characters shown of long text values (see `DataColumns.long_text`)


class CompoundDetails(QWidget):
    """One compound (row) shown in full: its structure plus every column, transposed.

    The structure has a 2D tab and a 3D tab; the 3D conformer is only generated when
    asked for (then cached), so clicking through compounds stays fast. Datasets
    without molecules show only the columns.

    When several compounds are selected at once, `show_many` greys the card
    out with a message instead, since it shows one compound at a time.
    """

    def __init__(self, dataset: ToolkitDataset):
        super().__init__()
        self.dataset = dataset
        self.query: Molecule | None = None
        self.current: int | None = None
        self.showing_many = False  # the "N compounds" message is up
        self.svg_cache: dict[int, bytes] = {}
        # row index -> 3D molecule, or None when embedding failed
        self.mol_3d_cache: dict[int, Molecule | None] = {}

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.svg_widget = QSvgWidget()
        self.svg_widget.setMinimumSize(240, 180)

        # 3D tab: a "Generate 3D" page until this compound has a conformer
        self.generate_button = PrimaryButton("Generate 3D", filled=True)
        self.generate_button.clicked.connect(self.generate_3d)
        self.generate_label = QLabel()
        self.generate_label.setWordWrap(True)
        self.generate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        generate_page = QWidget()
        generate_layout = QVBoxLayout(generate_page)
        generate_layout.addStretch()
        generate_layout.addWidget(
            self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        generate_layout.addWidget(self.generate_label)
        generate_layout.addStretch()

        self.viewer_3d = Molecule3DView()
        self.stack_3d = QStackedWidget()
        self.stack_3d.addWidget(generate_page)
        self.stack_3d.addWidget(self.viewer_3d)

        self.structure_tabs = QTabWidget()
        self.structure_tabs.addTab(self.svg_widget, "2D")
        self.structure_tabs.addTab(self.stack_3d, "3D")
        self.structure_tabs.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)

        self.value_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        for key in dataset.columns.shown:
            label = QLabel("-")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setWordWrap(True)  # e.g. long SMILES or names
            self.value_labels[key] = label
            form.addRow(f"{key}:", label)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.structure_tabs, stretch=1)
        self.structure_tabs.setVisible(dataset.has_molecules)
        layout.addLayout(form)
        if not dataset.has_molecules:
            layout.addStretch()
        # the first category column (e.g. a series) is named in the title
        categories = dataset.columns.of_kind(CATEGORY)
        self.title_category = categories[0] if categories else None

        self._render(None)

    def set_query(self, query: Molecule | None):
        self.query = query
        self.svg_cache.clear()
        if not self.showing_many:
            self._render(self.current)

    def show_row(self, index: int | None):
        # Skip re-showing the same compound (e.g. re-selecting it after a filter change).
        if index != self.current or self.showing_many:
            self._render(index)

    def show_many(self, count: int):
        """Grey out the card with a note that `count` compounds are selected."""
        self._render(None)
        self.showing_many = True
        self.structure_tabs.setEnabled(False)
        self.title_label.setText(
            f"{count} compounds selected\n\n"
            "This panel shows one compound at a time. "
            "Select a single compound to see it here."
        )

    def svg(self, index: int) -> bytes:
        """The compound's 2D drawing (with any query highlighted), drawn once then
        cached. Empty when the row has no (readable) structure."""
        if index not in self.svg_cache:
            molecule = self.dataset.molecule(index)
            self.svg_cache[index] = (
                b""
                if molecule is None
                else molecule.draw(
                    "svg",
                    size=(400, 300),
                    highlight_query=self.query,
                    stereo_annotations=True,
                )
            )
        return self.svg_cache[index]

    def _render(self, index: int | None):
        self.current = index
        self.showing_many = False
        self.structure_tabs.setEnabled(True)
        self._show_3d()
        if index is None:
            self.title_label.setText("Select a compound to see it here")
            self.svg_widget.load(QByteArray())
            for label in self.value_labels.values():
                label.setText("-")
            return

        row = self.dataset.df.row(index, named=True)
        if self.dataset.has_molecules:
            self.svg_widget.load(QByteArray(self.svg(index)))
            # load() swaps in a new renderer config, so re-apply the aspect ratio.
            self.svg_widget.renderer().setAspectRatioMode(
                Qt.AspectRatioMode.KeepAspectRatio
            )

        title = self.dataset.columns.label(index)
        if self.title_category and row[self.title_category] is not None:
            title += f"  ({row[self.title_category]})"
        if self.dataset.has_molecules and self.dataset.molecule(index) is None:
            title += "\nNo valid structure"
        self.title_label.setText(title)
        long_text = self.dataset.columns.long_text
        for key, label in self.value_labels.items():
            text = format_value(row[key]) or "-"
            if key in long_text and len(text) > MAX_TEXT:
                text = text[:MAX_TEXT] + "…"  # e.g. a whole mol block
            label.setText(text)

    def generate_3d(self):
        """Embed the current compound in 3D and show it."""
        if self.current is None:
            return
        molecule = self.dataset.molecule(self.current)
        if molecule is not None:
            molecule = molecule.copy()
            try:
                molecule.convert_to_3d(keep_hydrogen=True, random_seed=0xF00D)
            except Molecule.ConformerGenerationError:
                molecule = None
        self.mol_3d_cache[self.current] = molecule
        self._show_3d()

    def _show_3d(self):
        index = self.current
        if index is not None and self.mol_3d_cache.get(index) is not None:
            self.viewer_3d.show_mol(self.mol_3d_cache[index])
            self.stack_3d.setCurrentWidget(self.viewer_3d)
            return

        self.viewer_3d.show_mol(None)
        self.stack_3d.setCurrentIndex(0)
        self.generate_button.setEnabled(
            index is not None and index not in self.mol_3d_cache
        )
        if index is None:
            self.generate_label.setText("Select a compound first")
        elif index in self.mol_3d_cache:
            self.generate_label.setText("3D embedding failed for this compound")
        else:
            self.generate_label.setText("")
