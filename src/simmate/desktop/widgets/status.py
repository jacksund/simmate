from PySide6.QtWidgets import QLabel, QProgressBar

from simmate.desktop import theme
from simmate.desktop.theme import rgba


def set_status(label: QLabel, text: str, ok: bool | None = None) -> None:
    """Shows `text` in `label`: green if `ok`, red if not ok, grey if None."""
    color = {True: theme.SUCCESS_COLOR, False: theme.ERROR_COLOR}.get(
        ok, theme.MUTED_COLOR
    )
    label.setStyleSheet(f"color: {color};")
    label.setWordWrap(True)
    label.setText(text)


def link(url: str, text: str) -> str:
    """Rich text for a link in the primary color, with an "opens elsewhere" arrow.

    Show it in a `QLabel(openExternalLinks=True)` so clicking opens the browser.
    """
    return (
        f'<a href="{url}" style="color: {theme.PRIMARY_COLOR}; '
        f'text-decoration: none;">{text}&nbsp;↗</a>'
    )


def note_label(text: str) -> QLabel:
    """A label of small, muted text, e.g. explaining the input above it."""
    label = QLabel(text, wordWrap=True)
    label.setStyleSheet(f"color: {theme.MUTED_COLOR}; font-size: 11px;")
    return label


def callout_style(color: str) -> str:
    """A tinted, outlined box of text in `color`, e.g. for an alert or a tip."""
    return f"""
QLabel {{
    color: {color}; background: {rgba(color, theme.HOVER_ALPHA)};
    border: 1px solid {color}; border-radius: 6px; padding: 8px 12px;
}}
"""


def progress_bar_style() -> str:
    """A slim, rounded bar in the primary color, on a tint of it."""
    return f"""
QProgressBar {{
    background: {rgba(theme.PRIMARY_COLOR, theme.HOVER_ALPHA)};
    border: none; border-radius: 4px;
}}
QProgressBar::chunk {{ background: {theme.PRIMARY_COLOR}; border-radius: 4px; }}
"""


def loading_bar() -> QProgressBar:
    """A hidden busy bar (no progress, just motion) to show while loading."""
    bar = QProgressBar(maximum=0, textVisible=False)
    bar.setStyleSheet(progress_bar_style())
    bar.setFixedHeight(8)
    bar.hide()
    return bar


def heading_label(text: str) -> QLabel:
    """A section's title, e.g. above a table on a page with several sections."""
    label = QLabel(text)
    label.setStyleSheet("font-size: 15px; font-weight: 600;")
    return label
