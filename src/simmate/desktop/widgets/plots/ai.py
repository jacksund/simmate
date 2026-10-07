"""A plot described in words, made by an AI (a prototype: the UI only, for now).

TODO: generate the plot. Where to look when implementing this:

- `simmate/apps/chatbot/tools/plotly.py`: the old version of this. It prompts the LLM
  with `df.head()` and the request (`get_plotly_script`), caches the script it
  returns by request + columns (so changing filters doesn't call the LLM again).
  Get the LLM from `simmate/apps/chatbot/llm.py:get_llm` (that module's own
  `from .utils import get_llm` is stale: there's no `tools/utils.py`).
- `simmate/apps/analysis_dashboard/plot_constructors/ai_chatbot.py`: how the old
  streamlit dashboard offered it as one more plot type.
- `simmate/desktop/widgets/dataset_chat.py`: a chat UI, if this grows into a
  back-and-forth ("now color it by series").

Rather than running plotly code the LLM writes (as the old version did), ask it for
JSON naming one of `PLOT_TYPES` and its settings:

    {"type": "Scatter", "config": {"x": "cLogP", "y": "pIC50", "color": "series"}}

Build the prompt from each type's `description` and declared settings (the names
in `PlotPanel.settings`, with each combo's options) and the dataset's
`DataColumns.kinds`. Then swap this pane's content for a panel of that type and
`apply_config` the settings: the plot then hovers, selects and filters like any
other, which a plotly figure couldn't. Run the LLM call off the UI thread (e.g. a
`QThread`, like the dataset downloads) and show a busy state on the button meanwhile.
"""

from collections.abc import Callable

import polars
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget

from simmate.desktop import theme
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.inputs import input_style
from simmate.desktop.widgets.plots.base import PlotPanel


class AiPlotPanel(PlotPanel):
    """Describe a plot in words to have it made (not working yet: see this module)."""

    display_name = "Describe to AI"
    title = "AI plot"
    description = "Describe the plot you want, and have it made for you"
    preview = True

    def __init__(
        self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None = None
    ):
        super().__init__(df, svg_of)
        self._build(None)

        heading = QLabel("Describe the plot you want")
        font = heading.font()
        font.setBold(True)
        heading.setFont(font)
        self.request_input = QLineEdit()
        self.request_input.setPlaceholderText(
            "A scatter plot of pIC50 vs cLogP, by series…"
        )
        self.request_input.setStyleSheet(input_style())
        self.request_input.setMaximumWidth(420)
        self.generate_button = PrimaryButton("Generate", filled=True)
        self.generate_button.setEnabled(False)  # TODO: see this module's docstring
        self.generate_button.setToolTip("Not available yet")
        note = QLabel("Making plots from a description isn't available yet.")
        note.setStyleSheet(f"color: {theme.MUTED_COLOR};")

        form = QWidget()
        layout = QVBoxLayout(form)
        layout.addStretch()
        for widget in (heading, self.request_input, self.generate_button, note):
            layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        layout.setSpacing(10)
        self.request_input.setMinimumWidth(320)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
