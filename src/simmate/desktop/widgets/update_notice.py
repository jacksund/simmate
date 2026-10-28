import platform
import sys
from pathlib import Path

import requests
from packaging.version import Version
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

import simmate
from simmate.config import settings
from simmate.desktop import theme
from simmate.desktop.build import get_release_filename
from simmate.desktop.widgets.background import BackgroundTask
from simmate.desktop.widgets.confirm_dialog import confirm
from simmate.desktop.widgets.dataset_browser import display_path
from simmate.desktop.widgets.dataset_downloads import ASSETS_URL, download_file
from simmate.desktop.widgets.status import link, progress_bar_style
from simmate.utils import get_latest_version, logger


class UpdateNotice(QWidget):
    """
    Checks for a newer Simmate Desktop on startup and offers to download it to the
    config folder (`~/simmate/desktop` by default), for the window's status bar.
    It stays hidden until there's an update to show.

    Only packaged apps (from `simmate desktop build`) check, since pip installs
    update through pip. The newest version is the latest GitHub release, but only
    once its build for this OS is on the CDN: `simmate desktop upload` is run by
    hand on each OS, so a build can lag behind its release.
    """

    def __init__(self):
        super().__init__()
        self.folder = settings.config_directory / "desktop"

        self.note = QLabel(openExternalLinks=True)  # file:// opens the file explorer
        self.bar = QProgressBar(maximum=0, textVisible=False)  # busy until size known
        self.bar.setStyleSheet(progress_bar_style())
        self.bar.setFixedSize(160, 8)
        self.amount = QLabel()
        self.cancel = QLabel(
            f'<a href="cancel" style="color: {theme.PRIMARY_COLOR}; '
            'text-decoration: none;">Cancel</a>'
        )
        for label in [self.note, self.amount]:
            label.setStyleSheet(f"color: {theme.MUTED_COLOR};")
        for widget in [self.bar, self.amount, self.cancel]:
            widget.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(10)
        for widget in [self.note, self.bar, self.amount, self.cancel]:
            layout.addWidget(widget)
        self.hide()

        if getattr(sys, "frozen", False):  # set by PyInstaller builds
            task = BackgroundTask(lambda task: self._find_update(), self)
            task.finished.connect(self._offer_update)
            task.failed.connect(
                lambda error: logger.warning(f"Unable to check for updates: {error}")
            )
            task.start()

    def _find_update(self) -> tuple[str, str] | None:
        """The (version, url) of a newer build for this OS, if there is one. Runs on
        a background thread."""
        latest = get_latest_version()
        # A build ahead of the latest release (e.g. before it's published) should
        # never be offered an older version
        if Version(latest) <= Version(simmate.__version__):
            return None
        url = f"{ASSETS_URL}/desktop/{get_release_filename(latest)}"
        if not requests.head(url, timeout=10, allow_redirects=True).ok:
            return None  # not uploaded for this OS yet
        return latest, url

    def _offer_update(self, update: tuple[str, str] | None):
        if update is None:
            return
        version, url = update
        target = self.folder / url.rsplit("/", 1)[-1]
        if target.exists():  # downloaded on an earlier launch, but not opened yet
            self._show_downloaded(version, target)
            return
        if confirm(
            self.window(),
            "Update available",
            f"Simmate Desktop v{version} is available (you have "
            f"v{simmate.__version__}). Download it to {display_path(self.folder)}?",
            yes="Download",
            no="Not now",
        ):
            self._download(version, url, target)

    def _download(self, version: str, url: str, target: Path):
        self.folder.mkdir(parents=True, exist_ok=True)
        task = BackgroundTask(lambda task: download_file(url, target, task), self)
        self.cancel.linkActivated.connect(lambda _: task.cancel())

        self.note.setText(f"Downloading Simmate Desktop v{version}…")
        self.amount.setText("Starting…")
        for widget in [self.bar, self.amount, self.cancel, self]:
            widget.show()

        def on_progress(done: int, total: int):
            if total:
                self.bar.setMaximum(1000)
                self.bar.setValue(int(1000 * done / total))
                self.amount.setText(f"{done / 1e6:,.0f} MB of {total / 1e6:,.0f} MB")
            else:
                self.amount.setText(f"{done / 1e6:,.0f} MB")

        def on_finished(path: Path | None):
            for widget in [self.bar, self.amount, self.cancel]:
                widget.hide()
            if path is None:  # cancelled
                self.hide()
                return
            # Linux and macOS only run files marked as executable
            if platform.system() != "Windows":
                path.chmod(path.stat().st_mode | 0o111)
            self._show_downloaded(version, path)
            if confirm(
                self.window(),
                "Update downloaded",
                f"Saved to {display_path(path)}. Close this version and run the "
                "new one from there.",
                yes="Open folder",
                no="Close",
            ):
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.folder)))

        def on_failed(error: str):
            for widget in [self.bar, self.amount, self.cancel]:
                widget.hide()
            self.note.setStyleSheet(f"color: {theme.ERROR_COLOR};")
            self.note.setText(f"Update download failed: {error}")

        task.progress.connect(on_progress)
        task.finished.connect(on_finished)
        task.failed.connect(on_failed)
        task.start()

    def _show_downloaded(self, version: str, path: Path):
        folder_url = QUrl.fromLocalFile(str(path.parent)).toString()
        self.note.setText(
            f"Simmate Desktop v{version} is downloaded to "
            f"{display_path(path.parent)} &nbsp;·&nbsp; {link(folder_url, 'Open folder')}"
        )
        self.show()
