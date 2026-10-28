from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.dataset_browser import UPLOAD_FILTER
from simmate.desktop.widgets.plot_toolbar import folder_icon, plus_icon
from simmate.desktop.widgets.status import (
    heading_label,
    loading_bar,
    note_label,
    set_status,
)

CARD_WIDTH = 620  # px


class DatasetStart(QWidget):
    """
    The Toolkit tab before a dataset is open: ways to pick one, plus a loading bar
    and message while it opens.

    - `sample_requested`: open the sample dataset, for trying out the Toolkit.
    - `datasets_requested`: go to the Datasets tab, for the official datasets.
    - `upload_requested(path)`: a file the user chose to add and open.
    """

    sample_requested = Signal()
    datasets_requested = Signal()
    upload_requested = Signal(Path)

    def __init__(self):
        super().__init__()
        intro = QLabel(
            "Plot, filter, and search a table of molecules, or any other tabular data."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {theme.MUTED_COLOR};")

        self.sample_button = PrimaryButton("Open sample", filled=True)
        self.sample_button.clicked.connect(self.sample_requested)
        self.datasets_button = PrimaryButton(
            "Go to Datasets", icon=folder_icon(color=theme.PRIMARY_COLOR)
        )
        self.datasets_button.clicked.connect(self.datasets_requested)
        self.upload_button = PrimaryButton(
            "Upload file…", icon=plus_icon(color=theme.PRIMARY_COLOR)
        )
        self.upload_button.clicked.connect(self._choose_file)

        # one row per option (what it is, and its button), with a line between rows
        options = QGridLayout()
        options.setHorizontalSpacing(24)
        options.setVerticalSpacing(14)
        options.setColumnStretch(0, 1)
        for index, (title, text, button) in enumerate(
            [
                (
                    "Try the sample dataset",
                    (
                        "400 made-up compounds from six chemical series, with assay "
                        "results. It opens in seconds, so it's an easy way to learn "
                        "the Toolkit."
                    ),
                    self.sample_button,
                ),
                (
                    "Download a public dataset",
                    (
                        "Get catalogs like ChEMBL and the PDB ligands from the Datasets "
                        "tab, then click “Open in Toolkit”."
                    ),
                    self.datasets_button,
                ),
                (
                    "Upload your own data",
                    (
                        "An .sdf, .smi, .csv or .parquet file. A copy is kept in My "
                        "datasets (on the Datasets tab), so you can reopen it later."
                    ),
                    self.upload_button,
                ),
            ]
        ):
            row = 2 * index
            if index:
                divider = QFrame()
                divider.setFixedHeight(1)
                divider.setStyleSheet("background: palette(mid);")
                options.addWidget(divider, row - 1, 0, 1, 2)
            text_layout = QVBoxLayout()
            text_layout.setSpacing(4)
            option_title = QLabel(title)
            option_title.setStyleSheet("font-weight: 600;")
            text_layout.addWidget(option_title)
            text_layout.addWidget(note_label(text))
            options.addLayout(text_layout, row, 0)
            options.addWidget(button, row, 1, Qt.AlignmentFlag.AlignVCenter)

        self.loading_bar = loading_bar()
        self.message = QLabel()
        self.message.hide()

        card = QFrame(objectName="startCard")
        card.setStyleSheet(
            "#startCard { background: palette(base); border: 1px solid palette(mid); "
            f"border-radius: {theme.CORNER_RADIUS}px; }}"
        )
        card.setFixedWidth(CARD_WIDTH)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(12)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        header_layout.addWidget(heading_label("Open a dataset"))
        header_layout.addWidget(intro)
        card_layout.addLayout(header_layout)
        card_layout.addSpacing(12)
        card_layout.addLayout(options)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.loading_bar)
        card_layout.addWidget(self.message)

        # Centered with stretches, not alignment=AlignHCenter: an aligned item is
        # asked for its height at the page's full width, so the wrapped text above
        # gets one line's height and is cut off.
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()
        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addLayout(row)
        layout.addStretch()

    def set_loading(self, text: str):
        """Show a busy bar and `text` (e.g. "Opening …"), with the buttons disabled."""
        self.loading_bar.show()
        set_status(self.message, text)
        self.message.show()
        self._set_buttons_enabled(False)

    def set_error(self, text: str):
        """Stop loading and show `text` in red."""
        self.loading_bar.hide()
        set_status(self.message, text, False)
        self.message.show()
        self._set_buttons_enabled(True)

    def reset(self):
        """Back to the choices, with no loading bar or message."""
        self.loading_bar.hide()
        self.message.hide()
        self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled: bool):
        for button in (self.sample_button, self.datasets_button, self.upload_button):
            button.setEnabled(enabled)

    def _choose_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Upload a dataset", str(Path.home()), UPLOAD_FILTER
        )
        if file:
            self.upload_requested.emit(Path(file))
