from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from simmate.desktop import theme
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.plots.base import PlotPanel

BUTTONS_PER_ROW = 4


class PlotTypeChooser(QWidget):
    """What a new plot shows until its type is picked: a button per type."""

    chosen = Signal(str)

    def __init__(self, plot_types: dict[str, type[PlotPanel]]):
        super().__init__()
        label = QLabel("Choose a plot type")
        label.setStyleSheet(f"color: {theme.MUTED_COLOR};")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # the working types in a grid of same-width buttons, previews in a row below
        buttons = []
        previews = QHBoxLayout()
        previews.addStretch()
        for name, plot_type in plot_types.items():
            text = f"{name} (preview)" if plot_type.preview else name
            button = PrimaryButton(text, muted=plot_type.preview)
            button.setToolTip(plot_type.description)
            button.clicked.connect(lambda _=False, name=name: self.chosen.emit(name))
            if plot_type.preview:
                previews.addWidget(button)
            else:
                buttons.append(button)
        previews.addStretch()
        grid = QGridLayout()
        grid.setSpacing(8)
        width = max((b.sizeHint().width() for b in buttons), default=0)
        for i, button in enumerate(buttons):
            button.setMinimumWidth(width)
            grid.addWidget(button, i // BUTTONS_PER_ROW, i % BUTTONS_PER_ROW)
        row = QHBoxLayout()
        row.addStretch()
        row.addLayout(grid)
        row.addStretch()

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addLayout(row)
        layout.addSpacing(4)
        layout.addLayout(previews)
        layout.addStretch()
