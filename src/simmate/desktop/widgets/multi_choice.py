from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from simmate.desktop import theme
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import scroll_bar_style
from simmate.desktop.widgets.inputs import StyledCheckBox, input_style
from simmate.desktop.widgets.plot_toolbar import SettingsButton


class MultiChoice(QWidget):
    """A button that opens a checklist of `options`, to pick any number of them.

    `options` is a list, or a dict of lists to show under a heading each (e.g.
    {"Fingerprints": [...], "Columns": [...]}); empty sections are left out.

    While nothing is picked, the button reads `placeholder` in grey; it turns the
    primary color once something is picked. `changed` fires as boxes are checked
    or unchecked.
    """

    changed = Signal()

    MAX_LABEL = 24  # characters of the chosen options shown on the button

    def __init__(
        self,
        options: list[str] | dict[str, list[str]],
        placeholder: str = "All",
        tooltip: str = "Choose values to keep",
    ):
        super().__init__()
        self.placeholder = placeholder
        self.checkboxes: dict[str, StyledCheckBox] = {}
        # each section's list of boxes, which `add_options` appends to
        self.sections: dict[str | None, QVBoxLayout] = {}
        content = QWidget()
        content.setStyleSheet(input_style() + scroll_bar_style())
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8)
        clear = PrimaryButton("Clear", muted=True)
        clear.clicked.connect(lambda: self.set_chosen([]))
        self.content_layout.addWidget(clear)
        if isinstance(options, dict):
            for section, section_options in options.items():
                self.add_options(section_options, section)
        else:
            self.add_options(options)

        self.button = SettingsButton(content, tooltip=tooltip, text=" ")
        self.button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button)
        self._update_text()

    def add_options(self, options: list[str], section: str | None = None):
        """Add a box for each of `options` that has none yet, at the end of
        `section` (made, with its heading, if it's new)."""
        options = [option for option in options if option not in self.checkboxes]
        if not options:
            return
        if section not in self.sections:
            if section is not None:
                heading = QLabel(section)
                heading.setStyleSheet(
                    f"color: {theme.MUTED_COLOR}; font-weight: 600; margin-top: 4px;"
                )
                self.content_layout.addWidget(heading)
            self.sections[section] = QVBoxLayout()
            self.sections[section].setSpacing(8)
            self.content_layout.addLayout(self.sections[section])
        for option in options:
            checkbox = StyledCheckBox(option)
            checkbox.toggled.connect(self._on_toggled)
            self.sections[section].addWidget(checkbox)
            self.checkboxes[option] = checkbox

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
        text = ", ".join(chosen) if chosen else self.placeholder
        if len(text) > self.MAX_LABEL:
            text = f"{len(chosen)} selected"
        self.button.setText(text)
        # grey while nothing is picked, read by button_style
        if self.button.property("muted") != (not chosen):
            self.button.setProperty("muted", not chosen)
            self.button.style().unpolish(self.button)
            self.button.style().polish(self.button)
