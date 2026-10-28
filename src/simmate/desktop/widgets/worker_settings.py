import requests
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QWidget

from simmate.config import settings
from simmate.desktop import theme
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.inputs import input_style
from simmate.desktop.widgets.status import link, set_status

REQUIRED_SETTINGS = {
    "api_host": "API server",
    "api_key": "API key",
}
"""
The `settings.desktop` keys that workers can't start without, and their labels.
"""


def get_missing_settings() -> list[str]:
    """The `REQUIRED_SETTINGS` keys that aren't set."""
    return [key for key in REQUIRED_SETTINGS if not getattr(settings.desktop, key)]


def get_profile_url(host: str) -> str:
    """The user's profile page on a Simmate server, where they find their API key."""
    return f"{host.rstrip('/')}/accounts/profile/"


def check_api_server(host: str, api_key: str | None) -> tuple[bool, str]:
    """Checks that `host` is reachable and that `api_key` may run API workers."""
    try:
        response = requests.get(
            f"{host.rstrip('/')}/apps/compute/workers/check/",
            headers={"Authorization": f"Token {api_key}"} if api_key else {},
            allow_redirects=False,  # anonymous users are redirected to log in
            timeout=10,
        )
    except requests.RequestException as error:
        return False, f"Couldn't reach {host} ({type(error).__name__})."
    if response.status_code != 200:
        return False, f"Not signed in (HTTP {response.status_code}). Check the API key."
    data = response.json()
    if not data["can_run_workers"]:
        return False, f"Signed in as {data['username']}, who can't run API workers."
    return True, f"Signed in as {data['username']}."


class WorkerSettings(QWidget):
    """
    Edits the `desktop` section of the settings file (`~/simmate/settings.yaml`):
    the Simmate server that workers and the chatbot connect to, and the API key to
    sign in with. Missing required settings are shown in red.

    It reloads the file each time it's shown, as several of these forms can be
    open in the app (e.g. the Workers tab's and the Chatbot panel's).

    `saved` fires with the file's path after saving. Settings set by `SIMMATE__`
    env vars override the file, so then nothing can be saved.
    """

    saved = Signal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(input_style())
        self.api_host = QLineEdit(placeholderText="e.g. https://simmate.org")
        # Wide enough for a URL or key. Set on the input, as popouts size to the
        # form's size hint, which a minimum width on the form itself doesn't change.
        self.api_host.setMinimumWidth(320)
        self.api_key = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.api_key_hint = QLabel(openExternalLinks=True)  # opens the browser
        self.message = QLabel()
        test_button = PrimaryButton("Test connection")
        test_button.clicked.connect(self.test_connection)
        self.save_button = PrimaryButton("Save", filled=True)
        self.save_button.clicked.connect(self.save)

        self.form = QFormLayout(self)
        self.form.setContentsMargins(12, 12, 12, 12)
        self.form.setHorizontalSpacing(12)
        self.form.setVerticalSpacing(10)
        self.form.addRow("API server", self.api_host)
        self.form.addRow("API key", self.api_key)
        self.form.addRow("", self.api_key_hint)
        self.form.addRow(self.message)
        self.form.addRow(test_button, self.save_button)
        self.load()

    def load(self):
        """Fills the form from the settings file, marking missing settings red."""
        settings.reload()
        desktop = settings.desktop
        self.api_host.setText(desktop.api_host or "")
        self.api_key.setText(desktop.api_key or "")

        missing = get_missing_settings()
        for key in REQUIRED_SETTINGS:
            field = getattr(self, key)
            field.setProperty("invalid", key in missing)
            field.style().polish(field)  # re-read the stylesheet for the property
            self.form.labelForField(field).setStyleSheet(
                f"color: {theme.ERROR_COLOR};" if key in missing else ""
            )
        show_hint = "api_key" in missing and bool(desktop.api_host)
        if show_hint:
            url = get_profile_url(desktop.api_host)
            set_status(
                self.api_key_hint,
                f"Find your API key on your {link(url, 'profile page')}.",
                False,
            )
        self.form.setRowVisible(self.api_key_hint, show_hint)

        editable = settings.settings_source != "environment variables"
        self.save_button.setEnabled(editable)
        if editable:
            set_status(self.message, "")
        else:
            set_status(
                self.message,
                "These are set by SIMMATE__ environment variables, which override "
                "the settings file, so they can't be changed here.",
                False,
            )

    def showEvent(self, event):
        # the settings may have been saved from another of these forms
        self.load()
        super().showEvent(event)

    def test_connection(self):
        set_status(self.message, "Testing…")
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QGuiApplication.processEvents()  # show "Testing…" before blocking
        try:
            ok, message = check_api_server(
                self.api_host.text().strip(),
                self.api_key.text().strip() or None,
            )
        finally:
            QGuiApplication.restoreOverrideCursor()
        set_status(self.message, message, ok)

    def save(self):
        user_settings = dict(settings.user_settings)
        user_settings["desktop"] = {
            "api_host": self.api_host.text().strip(),
            "api_key": self.api_key.text().strip() or None,
        }
        settings.write_settings(filename=settings.settings_file, settings=user_settings)
        self.load()
        set_status(self.message, "Saved", True)
        self.saved.emit(str(settings.settings_file))
