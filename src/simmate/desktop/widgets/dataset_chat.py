from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.theme import rgba
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import scroll_bar_style
from simmate.desktop.widgets.status import heading_label

GREETING = (
    "What data are you looking for? Describe what you want, and I'll ask "
    "follow-up questions if needed, then fetch it from the Simmate API."
)

# One bordered, rounded box (like the tables) holds the conversation, with the
# message box inset at its bottom, as in other chat apps. The message box's text
# area has no border of its own.
CHAT_STYLE = f"""
#chat {{
    background: palette(window); border: 1px solid palette(mid); border-radius: 6px;
}}
#composer {{
    background: palette(base); border: 1px solid palette(mid); border-radius: 6px;
}}
QScrollArea, #history {{ background: transparent; border: none; }}
#composer QPlainTextEdit {{ background: transparent; border: none; }}
{scroll_bar_style()}
"""


def _bubble_style(color: str, text_color: str = "palette(text)") -> str:
    return f"""
QLabel {{
    color: {text_color}; background: {rgba(color, theme.HOVER_ALPHA)};
    border-radius: 10px; padding: 8px 12px;
}}
"""


class _Bubble(QLabel):
    """
    One chat message: as wide as its text (up to `MAX_WIDTH`), then wrapped. It can
    still shrink further, so a long message never holds the window wide.
    """

    MAX_WIDTH = 480
    PADDING = 32  # left + right padding from the style, plus a little slack

    def __init__(self, text: str):
        super().__init__(text, wordWrap=True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def sizeHint(self) -> QSize:
        width = self.fontMetrics().horizontalAdvance(self.text()) + self.PADDING
        width = min(width, self.MAX_WIDTH)
        return QSize(width, self.heightForWidth(width))

    def minimumSizeHint(self) -> QSize:
        return QSize(
            min(self.sizeHint().width(), 160), super().minimumSizeHint().height()
        )


class _MessageInput(QPlainTextEdit):
    """A multi-line text box where Enter sends (and Shift+Enter starts a new line)."""

    def __init__(self, on_send):
        super().__init__()
        self.on_send = on_send

    def keyPressEvent(self, event):
        enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        if enter and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.on_send()
            return
        super().keyPressEvent(event)


class DatasetChat(QWidget):
    """
    A chat for describing the data you want: an assistant asks follow-up questions,
    then fetches it from the Simmate API into your datasets.

    Only the UI exists so far. Replies say the assistant isn't connected yet.
    """

    def __init__(self):
        super().__init__()
        self.setStyleSheet(CHAT_STYLE)

        history = QWidget(objectName="history")
        self.messages = QVBoxLayout(history)
        self.messages.setContentsMargins(12, 12, 12, 12)
        self.messages.setSpacing(10)
        self.messages.addStretch()  # messages stack from the top
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(history)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)  # the stylesheet draws it
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # the message box: a text area with the Send button inside its border
        self.input = _MessageInput(self.send)
        self.input.setPlaceholderText("Describe the data you want…")
        self.input.setFixedHeight(56)
        send_button = PrimaryButton("Send", filled=True)
        send_button.clicked.connect(self.send)
        composer = QFrame(objectName="composer")
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(4, 4, 8, 8)
        composer_layout.addWidget(self.input, stretch=1)
        composer_layout.addWidget(send_button, alignment=Qt.AlignmentFlag.AlignBottom)

        chat = QFrame(objectName="chat")
        chat_layout = QVBoxLayout(chat)
        chat_layout.setContentsMargins(1, 1, 1, 1)  # inside the border
        chat_layout.setSpacing(0)
        chat_layout.addWidget(self.scroll_area, stretch=1)
        composer_row = QHBoxLayout()
        composer_row.setContentsMargins(12, 0, 12, 12)
        composer_row.addWidget(composer)
        chat_layout.addLayout(composer_row)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(heading_label("Ask AI"))
        layout.addWidget(chat, stretch=1)

        self.add_message(GREETING, from_user=False)

    def add_message(self, text: str, from_user: bool, error: bool = False):
        """Adds a chat bubble: the user's on the right, the assistant's on the left."""
        bubble = _Bubble(text)
        if from_user:
            style = _bubble_style(theme.PRIMARY_COLOR)
        elif error:
            style = _bubble_style(theme.ERROR_COLOR, theme.ERROR_COLOR)
        else:
            style = _bubble_style(theme.MUTED_COLOR)
        bubble.setStyleSheet(style)
        row = QHBoxLayout()
        if from_user:
            row.addStretch()
        row.addWidget(bubble)
        if not from_user:
            row.addStretch()
        self.messages.insertLayout(self.messages.count() - 1, row)
        # scroll to it, once the layout has made room for it
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def send(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self.add_message(text, from_user=True)
        # TODO: send the conversation to the chatbot app (`simmate.apps.chatbot`),
        # which asks follow-up questions and then downloads the data it finds.
        self.add_message(
            "The assistant isn't connected yet, so it can't fetch data. For now, "
            "try the ready-made downloads above.",
            from_user=False,
            error=True,
        )
