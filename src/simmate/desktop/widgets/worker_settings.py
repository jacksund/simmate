import requests
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from simmate.config import settings
from simmate.desktop import theme
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.inputs import StyledCheckBox, input_style
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


class ContributeToggle(QWidget):
    """
    A check box for whether workers also run other users' jobs (the default), with
    a line of muted text explaining it.
    """

    def __init__(self):
        super().__init__()
        self.check_box = StyledCheckBox("Run jobs from other users")
        note = QLabel(
            "Your workers help run jobs submitted by others, and you earn for the "
            "compute you share. Turn this off to run only your own jobs.",
            wordWrap=True,
        )
        note.setStyleSheet(f"color: {theme.MUTED_COLOR}; font-size: 11px;")
        note.setContentsMargins(24, 0, 0, 0)  # lined up with the check box's text
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.check_box)
        layout.addWidget(note)

    def isChecked(self) -> bool:
        return self.check_box.isChecked()

    def setChecked(self, checked: bool):
        self.check_box.setChecked(checked)


class WorkerSettings(QWidget):
    """
    Edits the `desktop` section of the settings file (`~/simmate/settings.yaml`):
    which Simmate server workers connect to, and whether they run other users' jobs
    by default. Missing required settings are shown in red.

    `saved` fires with the file's path after saving. Settings set by `SIMMATE__`
    env vars override the file, so then nothing can be saved.
    """

    saved = Signal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(input_style())
        self.setMinimumWidth(460)
        self.api_host = QLineEdit(placeholderText="e.g. https://simmate.org")
        self.api_key = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.api_key_hint = QLabel(openExternalLinks=True)  # opens the browser
        self.contribute = ContributeToggle()
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
        self.form.addRow("", self.contribute)
        self.form.addRow(self.message)
        self.form.addRow(test_button, self.save_button)
        self.load()

    def load(self):
        """Fills the form from the settings file, marking missing settings red."""
        settings.reload()
        desktop = settings.desktop
        self.api_host.setText(desktop.api_host or "")
        self.api_key.setText(desktop.api_key or "")
        self.contribute.setChecked(desktop.contribute)

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
            "contribute": self.contribute.isChecked(),
        }
        settings.write_settings(filename=settings.settings_file, settings=user_settings)
        self.load()
        set_status(self.message, "Saved", True)
        self.saved.emit(str(settings.settings_file))
