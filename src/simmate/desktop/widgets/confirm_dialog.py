from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.widgets.button import PrimaryButton

DIALOG_WIDTH = 420  # px
SHADOW_MARGIN = 16  # px of see-through room around the card for its shadow


class ConfirmDialog(QDialog):
    """
    A yes/no question in the app's style: a rounded card with a bold title, the
    question below it, and the buttons at the bottom ("Yes" filled, on the left).
    Escape or clicking "No" declines. Use `confirm` to ask and get the answer.
    """

    def __init__(
        self,
        parent: QWidget,
        title: str,
        text: str,
        yes: str = "Yes",
        no: str = "No",
    ):
        super().__init__(parent)
        # Frameless and see-through, so the card can round its corners and cast a
        # shadow, like the main window and the settings panels.
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(title)
        self.setModal(True)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 15px; font-weight: 600;")
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"color: {theme.MUTED_COLOR}; line-height: 140%;")

        yes_button = PrimaryButton(yes, filled=True)
        yes_button.setDefault(True)  # Enter confirms
        yes_button.clicked.connect(self.accept)
        no_button = PrimaryButton(no, muted=True)
        no_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch()
        buttons.addWidget(yes_button)
        buttons.addWidget(no_button)

        card = QFrame(objectName="confirmCard")
        card.setStyleSheet(
            "#confirmCard { background: palette(window); border: 1px solid "
            f"palette(mid); border-radius: {theme.CORNER_RADIUS}px; }}"
        )
        shadow = QGraphicsDropShadowEffect(blurRadius=24, offset=QPointF(0, 4))
        shadow.setColor(QColor(0, 0, 0, 70))
        card.setGraphicsEffect(shadow)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(10)
        card_layout.addWidget(title_label)
        card_layout.addWidget(text_label)
        card_layout.addSpacing(10)
        card_layout.addLayout(buttons)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*[SHADOW_MARGIN] * 4)
        layout.addWidget(card)
        self.setFixedWidth(DIALOG_WIDTH + 2 * SHADOW_MARGIN)

    def showEvent(self, event):
        # Centered over the window. (On Wayland the compositor places dialogs
        # itself, which also centers them on their parent.)
        self.adjustSize()
        window = self.parentWidget().window()
        center = window.mapToGlobal(window.rect().center())
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)
        super().showEvent(event)


def confirm(
    parent: QWidget, title: str, text: str, yes: str = "Yes", no: str = "No"
) -> bool:
    """Ask a yes/no question in a `ConfirmDialog`, and return whether the user
    said yes."""
    return (
        ConfirmDialog(parent, title, text, yes, no).exec()
        == QDialog.DialogCode.Accepted
    )
