"""The Toolkit's Chatbot panel: a chat about the open dataset (a prototype: the UI
only, for now).

TODO: get replies from the chatbot app (`simmate.apps.chatbot`) through its REST API.
Where to look and what to send when implementing this:

- Post to the server in `settings.desktop.api_host`, signed in with
  `settings.desktop.api_key` (an `Authorization: Token <key>` header, like
  `worker_settings.check_api_server`). The panel already says when they're missing
  (and its gear edits them); once replies come from the server, `send` should
  refuse while they are.
- Send `ChatbotPanel.history` (the messages so far, as dicts of "role", "content",
  and "script") and a description of the dataset rather than its rows: its name,
  row count, each column's kind (`DataColumns.kinds`) and dtype, its molecule
  column, and a few rows (`df.head()`).
- Expect `{"content": "<markdown>", "script": "<python>" or null}` back, i.e. the
  server pulls the script out of the LLM's reply. Its prompt should give the LLM
  the rules for scripts in `ScriptCard`'s docstring.
- Request in the `BackgroundTask` that makes the demo reply now (with a timeout),
  and raise on a failed request so `_on_reply_failed` shows it.
- Later: send a script's output (or error) back with the next message, so the
  assistant can see what its script did and fix it.
"""

import functools
import html
import io
import time

import polars
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.data import ToolkitDataset
from simmate.desktop.widgets.background import BackgroundTask
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import scroll_bar_style
from simmate.desktop.widgets.dataset_chat import (
    ChatBubble,
    ChatHeader,
    MessageInput,
    bubble_style,
)
from simmate.desktop.widgets.status import callout_style, loading_bar, note_label

# Every reply until the panel is connected to the chatbot app (see this module).
DEMO_REPLY = {
    "content": (
        "The chatbot isn't connected yet, so this is a sample reply. Replies can "
        "include a Python script to run on the dataset, like this one: it numbers "
        "the rows and summarizes the numeric columns. Click **Run** to try it."
    ),
    "script": """import polars as pl

# number the rows, as a new column
df = df.with_columns(row_number=pl.int_range(1, pl.len() + 1))

print(f"{df.height:,} rows, now with a row_number column")
print(df.select(pl.selectors.numeric()).describe())
""",
}


def chatbot_style() -> str:
    return f"""
#panelTitle {{ color: {theme.MUTED_COLOR}; font-weight: bold; }}
/* see-through, so the window shows behind the panel like the rest of the app */
#chatScroll, #chatHistory {{ background: transparent; }}
#composer, #scriptCard {{
    background: palette(base); border: 1px solid palette(mid); border-radius: 6px;
}}
#composer QPlainTextEdit {{ background: transparent; border: none; }}
#scriptTitle {{ color: {theme.MUTED_COLOR}; font-weight: 600; }}
#scriptCard QPlainTextEdit {{
    background: transparent; border: none; border-top: 1px solid palette(mid);
}}
#scriptOutput {{ color: {theme.MUTED_COLOR}; }}
{scroll_bar_style()}"""


class ChatbotPanel(QWidget):
    """The Toolkit's Chatbot column: a chat about the open dataset. Ask about its
    data, or for columns to add, and the assistant answers, often with a Python
    script to run on the dataset (see `ScriptCard`).

    Replies are all a demo for now (see this module). Its header (see `ChatHeader`)
    resets the chat and edits the Simmate server settings that the chatbot will
    need, saying when they're missing.

    `columns_added(added, replaced)` fires with the column names once a script's
    columns are in the dataset (see `ToolkitDataset.add_columns`).
    """

    columns_added = Signal(object, object)

    def __init__(self, dataset: ToolkitDataset):
        super().__init__()
        self.dataset = dataset
        # the conversation so far, sent with each new message (see this module)
        self.history: list[dict] = []
        self.reply_task: BackgroundTask | None = None
        self.setStyleSheet(chatbot_style())

        title = QLabel("Chatbot", objectName="panelTitle")
        font = title.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        title.setFont(font)
        self.header = ChatHeader(title)
        self.header.setContentsMargins(8, 8, 12, 8)
        self.header.reset_button.clicked.connect(self.reset_chat)

        # --- the conversation ---------------------------------------------------------
        history = QWidget(objectName="chatHistory")
        self.messages = QVBoxLayout(history)
        self.messages.setContentsMargins(8, 0, 12, 8)
        self.messages.setSpacing(12)
        self.messages.addStretch()  # messages stack from the top
        self.scroll_area = QScrollArea(objectName="chatScroll")
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidget(history)
        self.scroll_area.viewport().setAutoFillBackground(False)

        # --- footer: the message box, with the Send button inside its border ----------
        self.thinking_bar = loading_bar()
        self.thinking_note = note_label("Thinking…")
        self.thinking_note.hide()
        self.input = MessageInput(self.send)
        self.input.setPlaceholderText("Ask about this dataset…")
        self.input.setFixedHeight(56)
        self.send_button = PrimaryButton("Send", filled=True)
        self.send_button.clicked.connect(self.send)
        composer = QFrame(objectName="composer")
        composer_layout = QHBoxLayout(composer)
        composer_layout.setContentsMargins(4, 4, 8, 8)
        composer_layout.addWidget(self.input, stretch=1)
        composer_layout.addWidget(
            self.send_button, alignment=Qt.AlignmentFlag.AlignBottom
        )

        footer = QVBoxLayout()
        footer.setContentsMargins(8, 8, 12, 8)
        footer.setSpacing(8)
        footer.addWidget(self.thinking_note)
        footer.addWidget(self.thinking_bar)
        footer.addWidget(composer)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.scroll_area, stretch=1)
        layout.addLayout(footer)

        self.reset_chat()

    def reset_chat(self):
        """Clear the conversation, back to the greeting."""
        while self.messages.count() > 1:  # every message, then the stretch
            self.messages.takeAt(0).widget().deleteLater()
        self.history = []
        self.add_message(
            f"Ask me about {self.dataset.name}, such as what's in it or which "
            "columns to add. When it helps, I'll write a Python script you can run "
            "on the dataset.",
            from_user=False,
        )

    def send(self):
        text = self.input.toPlainText().strip()
        if not text or self.reply_task is not None:
            return
        self.input.clear()
        self.add_message(text, from_user=True)
        self.history.append({"role": "user", "content": text, "script": None})

        def work(_) -> dict:
            # TODO: post the conversation to the chatbot app (see this module)
            time.sleep(1)
            return DEMO_REPLY

        # Not parented to the panel, which is deleted if the dataset is closed while
        # waiting. Its connections to the panel's methods go with the panel, so the
        # reply is then dropped.
        self.reply_task = BackgroundTask(work)
        self.reply_task.finished.connect(self._on_reply)
        self.reply_task.failed.connect(self._on_reply_failed)
        self._set_waiting(True)
        self.reply_task.start()

    def add_message(
        self,
        text: str,
        from_user: bool,
        script: str | None = None,
        error: bool = False,
    ):
        """Adds a message: the user's in a bubble on the right, and the assistant's
        as full-width text (markdown), followed by its `script` if it has one."""
        message = QWidget()
        row = QVBoxLayout(message)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        if from_user:
            bubble = ChatBubble(text)
            bubble.setStyleSheet(bubble_style(theme.PRIMARY_COLOR))
            # kept off the left edge, so it reads as the user's side
            row.setContentsMargins(40, 0, 0, 0)
            row.addWidget(bubble, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            label = QLabel(
                text,
                wordWrap=True,
                textFormat=Qt.TextFormat.MarkdownText,
                openExternalLinks=True,
            )
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            if error:
                label.setStyleSheet(f"color: {theme.ERROR_COLOR};")
            row.addWidget(label)
        if script:
            card = ScriptCard(script, self.dataset)
            card.columns_added.connect(self.columns_added)
            row.addWidget(card)
        self.messages.insertWidget(self.messages.count() - 1, message)
        # scroll to it, once the layout has made room for it
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _on_reply(self, reply: dict):
        self.reply_task = None
        self._set_waiting(False)
        self.history.append({"role": "assistant", **reply})
        self.add_message(reply["content"], from_user=False, script=reply["script"])

    def _on_reply_failed(self, error: str):
        self.reply_task = None
        self._set_waiting(False)
        self.add_message(f"Couldn't get a reply: {error}", from_user=False, error=True)

    def _set_waiting(self, waiting: bool):
        self.thinking_note.setVisible(waiting)
        self.thinking_bar.setVisible(waiting)
        self.send_button.setEnabled(not waiting)
        # the reply would land in the cleared chat
        self.header.reset_button.setEnabled(not waiting)

    def _scroll_to_bottom(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())


class ScriptCard(QWidget):
    """A Python script from the assistant, run on the dataset with its Run button
    (it never runs on its own, as it can do anything on this computer). The script
    and what it printed share a bordered box, with how the run went below it.

    The rules for scripts (to give the LLM in its prompt):

    - `df` is the dataset, as a polars DataFrame.
    - To add or change columns, assign a new `df` with the same rows in the same
      order (e.g. `df = df.with_columns(...)`). Its new and changed columns are
      added to the dataset.
    - Anything printed shows below the script.

    `columns_added(added, replaced)` fires with the column names once the script's
    columns are in the dataset (see `ToolkitDataset.add_columns`).
    """

    columns_added = Signal(object, object)

    MAX_NAMES = 6  # columns named in the "Added" message

    def __init__(self, script: str, dataset: ToolkitDataset):
        super().__init__()
        self.script = script
        self.dataset = dataset
        self.task: BackgroundTask | None = None

        title = QLabel("Python", objectName="scriptTitle")
        self.copy_button = PrimaryButton("Copy", muted=True)
        self.copy_button.setToolTip("Copy the script")
        self.copy_button.clicked.connect(self.copy)
        self.run_button = PrimaryButton("Run", filled=True)
        self.run_button.setToolTip("Run the script on the dataset")
        self.run_button.clicked.connect(self.run)
        self.code = _CodeView(script)
        self.output = _CodeView(objectName="scriptOutput")  # what the script printed
        self.output.hide()
        self.loading_bar = loading_bar()
        # how the last run went: a primary-colored (done) or red (failed) callout
        self.result = QLabel(wordWrap=True, textFormat=Qt.TextFormat.RichText)
        self.result.hide()

        header = QHBoxLayout()
        header.setContentsMargins(10, 6, 6, 6)
        header.setSpacing(4)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.copy_button)
        header.addWidget(self.run_button)
        box = QFrame(objectName="scriptCard")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(1, 0, 1, 1)  # inside the border
        box_layout.setSpacing(0)
        box_layout.addLayout(header)
        box_layout.addWidget(self.code)
        box_layout.addWidget(self.output)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(box)
        layout.addWidget(self.loading_bar)
        layout.addWidget(self.result)

    def copy(self):
        QGuiApplication.clipboard().setText(self.script)
        self.copy_button.setText("Copied")
        QTimer.singleShot(
            1500, self.copy_button, lambda: self.copy_button.setText("Copy")
        )

    def run(self):
        """Run the script in the background on the dataset as it is now, then add
        the columns it made."""
        df = self.dataset.df
        script = self.script

        def work(_) -> tuple[str, polars.DataFrame | None, str | None]:
            # Returns what it printed, then the new and changed columns, or the error.
            # The script gets a `print` of its own, as redirecting stdout would also
            # catch prints from the rest of the app.
            output = io.StringIO()
            namespace = {"df": df, "print": functools.partial(print, file=output)}
            try:
                # only ever run from the Run button, on a script the user can see
                exec(compile(script, "<script>", "exec"), namespace)  # noqa: S102
                new_df = namespace["df"]
                if (
                    not isinstance(new_df, polars.DataFrame)
                    or new_df.height != df.height
                ):
                    raise ValueError(
                        "scripts can add or change columns, but `df` must stay a "
                        f"DataFrame of the same {df.height:,} rows"
                    )
                changed = [
                    key
                    for key in new_df.columns
                    if key not in df.columns
                    or not new_df[key].equals(df[key], check_dtypes=True)
                ]
            # BaseException also catches a script's `exit()` (SystemExit)
            except BaseException as error:
                return output.getvalue(), None, f"{type(error).__name__}: {error}"
            return output.getvalue(), new_df.select(changed), None

        # Not parented to the card, so the result is dropped if it's deleted mid-run
        # (see `ChatbotPanel.send`).
        self.task = BackgroundTask(work)
        self.task.finished.connect(self._on_finished)
        self.task.failed.connect(self._on_failed)
        self.run_button.setEnabled(False)
        self.result.hide()
        self.loading_bar.show()
        self.task.start()

    def _on_failed(self, error: str):
        self._on_finished(("", None, error))

    def _on_finished(self, result: tuple[str, polars.DataFrame | None, str | None]):
        self.task = None
        output, new, error = result
        self.run_button.setEnabled(True)
        self.loading_bar.hide()
        self.output.set_text(output.rstrip())
        self.output.setVisible(bool(output.strip()))

        if error:
            self.result.setStyleSheet(callout_style(theme.ERROR_COLOR))
            self.result.setText(f"<b>✗ The script failed</b><br>{html.escape(error)}")
        elif new.width:
            added, replaced = self.dataset.add_columns(new)
            self.columns_added.emit(added, replaced)
            # e.g. "Added 1 column, replaced 2 columns"
            message = ", ".join(
                f"{verb} {len(keys)} column" + ("" if len(keys) == 1 else "s")
                for verb, keys in [("added", added), ("replaced", replaced)]
                if keys
            ).capitalize()
            names = ", ".join(new.columns[: self.MAX_NAMES])
            if new.width > self.MAX_NAMES:
                names += f" and {new.width - self.MAX_NAMES} more"
            self.result.setStyleSheet(callout_style(theme.PRIMARY_COLOR))
            self.result.setText(f"<b>✓ {message}</b><br>{html.escape(names)}")
        else:
            self.result.setStyleSheet(callout_style(theme.PRIMARY_COLOR))
            self.result.setText("<b>✓ Done</b><br>The dataset's columns are unchanged.")
        self.result.show()


class _CodeView(QPlainTextEdit):
    """Read-only monospace text (a script or its output), as tall as its lines up
    to `MAX_LINES`, then scrolling. Long lines scroll sideways rather than wrap."""

    MAX_LINES = 14

    def __init__(self, text: str = "", **kwargs):
        super().__init__(readOnly=True, **kwargs)
        self.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.document().setDocumentMargin(8)
        self.set_text(text)

    def set_text(self, text: str):
        self.setPlainText(text)
        lines = min(self.blockCount(), self.MAX_LINES)
        self.setFixedHeight(
            lines * self.fontMetrics().lineSpacing()
            + 2 * int(self.document().documentMargin())
            + 14  # room for the sideways scroll bar (see `scroll_bar_style`)
        )
