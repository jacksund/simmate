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
from simmate.desktop.widgets.plot_toolbar import SettingsButton, reset_icon
from simmate.desktop.widgets.status import callout_style, heading_label
from simmate.desktop.widgets.worker_settings import (
    REQUIRED_SETTINGS,
    WorkerSettings,
    get_missing_settings,
)

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


def bubble_style(color: str, text_color: str = "palette(text)") -> str:
    return f"""
QLabel {{
    color: {text_color}; background: {rgba(color, theme.HOVER_ALPHA)};
    border-radius: 10px; padding: 8px 12px;
}}
"""


class ChatBubble(QLabel):
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


class MessageInput(QPlainTextEdit):
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


class ChatHeader(QWidget):
    """
    A chat's title row: `title`, then a "Reset chat" button (connect to its
    `reset_button`) and a gear for the Simmate server settings that the chatbot
    needs (the same form as the Workers tab's).

    While any of those settings are missing, the gear is red and a callout below the
    row says so. It checks again each time it's shown and after saving, as they can
    also be edited elsewhere in the app.
    """

    def __init__(self, title: QLabel):
        super().__init__()
        self.reset_button = PrimaryButton("Reset chat", muted=True)
        self.reset_button.setIcon(reset_icon())
        self.reset_button.setToolTip("Clear this chat and start over")
        server_settings = WorkerSettings()
        server_settings.saved.connect(self._check_settings)
        self.settings_button = SettingsButton(
            server_settings, tooltip="Simmate server settings"
        )
        self.settings_alert = QLabel(wordWrap=True)
        self.settings_alert.setStyleSheet(callout_style(theme.ERROR_COLOR))

        title_row = QHBoxLayout()
        title_row.setSpacing(2)  # the two buttons sit close together
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.reset_button)
        title_row.addWidget(self.settings_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(title_row)
        layout.addWidget(self.settings_alert)

    def _check_settings(self):
        """Show whether the server settings are missing, in the callout and gear."""
        missing = get_missing_settings()
        names = ", ".join(REQUIRED_SETTINGS[key] for key in missing)
        self.settings_alert.setText(
            f"The chatbot needs your Simmate account. Set the missing settings "
            f"({names}) with the gear button above."
        )
        self.settings_alert.setVisible(bool(missing))
        self.settings_button.set_alert(bool(missing))

    def showEvent(self, event):
        self._check_settings()
        super().showEvent(event)


class DatasetChat(QWidget):
    """
    A chat for describing the data you want: an assistant asks follow-up questions,
    then fetches it from the Simmate API into your datasets. Its header (see
    `ChatHeader`) resets the chat and edits the server settings it needs.

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
        self.input = MessageInput(self.send)
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

        self.header = ChatHeader(heading_label("Ask AI"))
        self.header.reset_button.clicked.connect(self.reset_chat)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.header)
        layout.addWidget(chat, stretch=1)

        self.reset_chat()

    def reset_chat(self):
        """Clear the conversation, back to the greeting."""
        while self.messages.count() > 1:  # every message, then the stretch
            self.messages.takeAt(0).widget().deleteLater()
        self.add_message(GREETING, from_user=False)

    def add_message(self, text: str, from_user: bool, error: bool = False):
        """Adds a chat bubble: the user's on the right, the assistant's on the left."""
        bubble = ChatBubble(text)
        if from_user:
            style = bubble_style(theme.PRIMARY_COLOR)
        elif error:
            style = bubble_style(theme.ERROR_COLOR, theme.ERROR_COLOR)
        else:
            style = bubble_style(theme.MUTED_COLOR)
        bubble.setStyleSheet(style)
        message = QWidget()
        row = QHBoxLayout(message)
        row.setContentsMargins(0, 0, 0, 0)
        if from_user:
            row.addStretch()
        row.addWidget(bubble)
        if not from_user:
            row.addStretch()
        self.messages.insertWidget(self.messages.count() - 1, message)
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
