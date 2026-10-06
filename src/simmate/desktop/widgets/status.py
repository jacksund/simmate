from PySide6.QtWidgets import QLabel

from simmate.desktop import theme


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
