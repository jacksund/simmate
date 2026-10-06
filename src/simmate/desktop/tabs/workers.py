import os
import threading
from collections.abc import Callable
from functools import partial
from uuid import uuid4

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import simmate
from simmate.config import settings
from simmate.desktop import theme
from simmate.desktop.theme import rgba
from simmate.desktop.widgets import (
    PrimaryButton,
    SettingsButton,
    WorkerSettings,
    input_style,
    note_label,
    plus_icon,
    reset_icon,
    scroll_bar_style,
    set_status,
    stop_icon,
    table_style,
    trash_icon,
)
from simmate.desktop.widgets.worker_settings import (
    REQUIRED_SETTINGS,
    ContributeToggle,
    get_missing_settings,
)

WORKER_IMAGE = f"docker.io/jacksund/simmate-worker:v{simmate.__version__}"
"""
The image every worker runs: the Simmate release matching this app.
"""

# the logs match the worker table: bordered and rounded, on the window's background
LOGS_STYLE = """
QPlainTextEdit {
    background: palette(window); border: 1px solid palette(mid);
    border-radius: 6px; padding: 8px;
}
"""
# for the message saying why workers can't start yet
# a slim, rounded bar in the primary color, on a tint of it
LOADING_STYLE = f"""
QProgressBar {{
    background: {rgba(theme.PRIMARY_COLOR, theme.HOVER_ALPHA)};
    border: none; border-radius: 4px;
}}
QProgressBar::chunk {{ background: {theme.PRIMARY_COLOR}; border-radius: 4px; }}
"""


def _callout_style(color: str) -> str:
    """A tinted, outlined box of text in `color`, e.g. for an alert or a tip."""
    return f"""
QLabel {{
    color: {color}; background: {rgba(color, theme.HOVER_ALPHA)};
    border: 1px solid {color}; border-radius: 6px; padding: 8px 12px;
}}
"""


def _launcher():
    """
    `simmate.compute.launcher`, imported on first use. Importing `simmate.compute`
    sets up Django, which must not happen before Qt WebEngine starts (web views
    then hang), so this waits until a worker action needs it.
    """
    from simmate.database import connect  # isort:skip
    from simmate.compute import launcher

    return launcher


class WorkersTab(QWidget):
    """
    Starts containerized API workers (via Podman or Docker) and lists them, with
    their logs. Where they connect, and whether they run other users' jobs by
    default, are set by
    `settings.desktop` (edited from the gear button). While workers can't start
    (e.g. a setting is missing), a message above the list says why.

    Containers keep running after the app closes, and are listed again the next
    time it opens.
    """

    status = Signal(str)
    # fires (from a background thread) with the podman/docker path, or None
    _engine_found = Signal(object)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(input_style())
        self.engine: str | None = None  # path to podman/docker, if running
        self.engine_checked = False
        self.loading = False
        self._engine_found.connect(self._on_engine_found)
        self.containers: list[tuple[str, str, str]] = []  # (id, name, status)
        self.starting = 0  # workers started but not yet listed
        cores = os.cpu_count() or 1
        # leave two cores free for this app and the rest of the desktop
        self.max_workers = max(cores - 2, 1)

        # --- the "Start worker(s)" popout ---
        start_form = QWidget()
        # the popout floats over the window, so it doesn't inherit this tab's style
        start_form.setStyleSheet(input_style())
        # fixed, so the wrapped text below gets its full height when the panel sizes
        start_form.setFixedWidth(400)
        intro = QLabel(
            "Each worker runs in its own Podman or Docker container and completes "
            "jobs one at a time. Workers keep running after you close the app.",
            wordWrap=True,
        )
        intro.setStyleSheet(_callout_style(theme.PRIMARY_COLOR))
        self.count = QSpinBox(minimum=1, maximum=self.max_workers)
        self.count_note = note_label("")
        self.contribute = ContributeToggle()
        self.message = QLabel()
        self.start_button = PrimaryButton("Start", filled=True)
        self.start_button.clicked.connect(self.start_workers)
        # evenly spaced sections: the intro, the count (with its note), the toggle
        count_row = QHBoxLayout()
        count_row.setSpacing(12)
        count_row.addWidget(QLabel("Workers"))
        count_row.addWidget(self.count, stretch=1)
        count_section = QVBoxLayout()
        count_section.setSpacing(4)
        count_section.addLayout(count_row)
        count_section.addWidget(self.count_note)
        form = QVBoxLayout(start_form)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(16)
        form.addWidget(intro)
        form.addLayout(count_section)
        form.addWidget(self.contribute)
        form.addWidget(self.message)
        form.addWidget(self.start_button)
        self.start_popout = SettingsButton(
            start_form,
            tooltip="Start new workers",
            text="Start worker(s)",
            icon=plus_icon(color=theme.PRIMARY_COLOR),
        )
        # each time it opens, start from the default in the settings
        self.start_popout.toggled.connect(
            lambda open: open
            and self.contribute.setChecked(settings.desktop.contribute)
        )

        # --- toolbar ---
        refresh_button = PrimaryButton("Refresh", muted=True, icon=reset_icon())
        refresh_button.clicked.connect(self.check_engine)
        self.stop_all_button = PrimaryButton("Stop all", muted=True, icon=stop_icon())
        self.stop_all_button.clicked.connect(self.stop_all)
        self.remove_all_button = PrimaryButton(
            "Remove all", muted=True, icon=trash_icon()
        )
        self.remove_all_button.clicked.connect(self.remove_all)
        worker_settings = WorkerSettings()
        worker_settings.saved.connect(self._on_settings_saved)
        buttons = QHBoxLayout()
        buttons.addWidget(self.start_popout)
        buttons.addWidget(refresh_button)
        buttons.addStretch()
        buttons.addWidget(self.stop_all_button)
        buttons.addWidget(self.remove_all_button)
        self.settings_button = SettingsButton(
            worker_settings, tooltip="Worker settings"
        )
        buttons.addWidget(self.settings_button)

        self.alert = QLabel(wordWrap=True)
        self.alert.setStyleSheet(_callout_style(theme.ERROR_COLOR))
        self.alert.hide()

        self.loading_bar = QProgressBar(maximum=0, textVisible=False)  # busy
        self.loading_bar.setStyleSheet(LOADING_STYLE)
        self.loading_bar.setFixedHeight(8)
        self.loading_bar.hide()

        # --- worker list, styled like the Toolkit's compound table ---
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Status", ""])
        self.table.setStyleSheet(table_style())
        self.table.setFrameShape(QFrame.Shape.NoFrame)  # the stylesheet draws it
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(40)
        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_logs)

        self.logs = QPlainTextEdit(readOnly=True)
        self.logs.setStyleSheet(LOGS_STYLE + scroll_bar_style())
        self.logs.setFrameShape(QFrame.Shape.NoFrame)
        self.logs.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.logs.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.logs.setPlaceholderText("Select a worker to see its logs")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.logs)
        splitter.setSizes([400, 300])
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.addLayout(buttons)
        layout.addWidget(self.loading_bar)
        layout.addWidget(self.alert)
        layout.addWidget(splitter)
        self._update_table()  # disables "Stop all" and "Remove all" until listed

    def showEvent(self, event):
        super().showEvent(event)
        if self.engine_checked:
            self._update_form()
            self.refresh()
        else:
            self.check_engine()

    def _update_form(self):
        if self.loading:
            set_status(self.message, "Loading…")
            self.message.show()
            self.start_button.setEnabled(False)
            self.start_popout.setEnabled(False)
            self.alert.hide()
            return
        missing = get_missing_settings()
        self.settings_button.set_alert(bool(missing))
        if not self.engine:
            problem = (
                "Podman or Docker isn't running.<br>"
                "Install and start one of them, then click Refresh."
            )
        elif missing:
            names = ", ".join(REQUIRED_SETTINGS[key] for key in missing)
            problem = (
                f"Required settings are missing: {names}.<br>"
                "Fix this with the settings (gear) button in the top right."
            )
        else:
            problem = ""
        self.alert.setText(problem)
        self.alert.setVisible(bool(problem))
        self.start_popout.setEnabled(not problem)

        # at most `max_workers` run at once (the cores, minus two left free)
        running = sum(_is_running(status) for _, _, status in self.containers)
        available = self.max_workers - running - self.starting
        self.count.setMaximum(max(available, 1))
        self.count_note.setText(
            f"Up to {self.max_workers} at once: this computer's {os.cpu_count()} "
            f"cores, minus two kept free for other apps. {running} running now."
        )
        if not problem and available <= 0:
            problem = "All worker slots are in use. Stop a worker to start another."
        set_status(self.message, problem, False)
        self.message.setVisible(bool(problem))  # no gap above Start when empty
        self.start_button.setEnabled(not problem)

    def start_workers(self):
        self.start_popout.setChecked(False)
        desktop = settings.desktop
        launcher = _launcher()
        env = launcher.get_container_env(desktop.api_host, desktop.api_key)
        # TODO: pass on `self.contribute.isChecked()` once the server can limit an
        # API worker to its owner's jobs (work items don't record who submitted them)
        for _ in range(self.count.value()):
            self.starting += 1
            name = f"simmate-worker-{uuid4().hex[:8]}"
            command = launcher.get_container_command(
                self.engine, name, WORKER_IMAGE, [], env
            )
            self.status.emit(
                f"Starting {name}... (the first one downloads the worker image)"
            )
            self._run(command, partial(self._started, name), env=env)

    def _started(self, name: str, exit_code: int, output: str):
        self.starting -= 1
        if exit_code:
            self.status.emit(f"Couldn't start {name}: {output.strip()}")
        else:
            self.status.emit(f"Started {name}")
        self.refresh()

    # -------------------------------------------------------------------------
    # the worker list
    # -------------------------------------------------------------------------

    def _on_settings_saved(self, path: str):
        self.status.emit(f"Worker settings saved to {path}")
        self._update_form()

    def check_engine(self):
        """
        Looks for a running podman/docker, then refreshes. This (and setting up
        Django on first use) takes a few seconds, so it runs in the background
        while a busy bar shows.
        """
        if self.loading:
            return
        self.loading = True
        self.loading_bar.show()
        self._update_form()
        threading.Thread(
            target=lambda: self._engine_found.emit(_launcher().find_container_engine()),
            daemon=True,
        ).start()

    def _on_engine_found(self, engine: str | None):
        self.engine = engine
        self.engine_checked = True
        self.loading = False
        self.loading_bar.hide()
        self._update_form()
        self.refresh()

    def refresh(self):
        """Re-lists the worker containers."""
        if not self.engine:
            self.containers = []
            self._update_table()
            return

        def done(exit_code: int, output: str):
            lines = output.splitlines() if exit_code == 0 else []
            self.containers = [tuple(line.split("\t")) for line in lines if line]
            self._update_table()

        self._run(_launcher().get_list_containers_command(self.engine), done)

    def _update_table(self):
        selected = self._selected()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.containers))
        for row, (id, name, status) in enumerate(self.containers):
            for column, text in enumerate([name, status]):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, id)
                self.table.setItem(row, column, item)
            self.table.setCellWidget(row, 2, self._row_actions(id, status))
            if id == selected:
                self.table.selectRow(row)
        self.table.blockSignals(False)
        running = [id for id, _, status in self.containers if _is_running(status)]
        self.stop_all_button.setEnabled(bool(running))
        self.remove_all_button.setEnabled(bool(self.containers))
        self._update_form()  # how many more workers can start

    def _row_actions(self, id: str, status: str) -> QWidget:
        """Stop and Remove buttons for one container."""
        stop_button = PrimaryButton("Stop", muted=True, icon=stop_icon())
        stop_button.setEnabled(_is_running(status))
        stop_button.clicked.connect(lambda: self._container_action(["stop"], [id]))
        remove_button = PrimaryButton("Remove", muted=True, icon=trash_icon())
        remove_button.clicked.connect(
            lambda: self._container_action(["rm", "--force"], [id])
        )
        actions = QWidget()
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.addWidget(stop_button)
        layout.addWidget(remove_button)
        return actions

    def _selected(self) -> str | None:
        """The id of the selected container."""
        items = self.table.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    def show_logs(self):
        selected = self._selected()
        if not selected:
            self.logs.clear()
            return
        self._run(
            [self.engine, "logs", "--tail", "500", selected],
            lambda _, output: self._selected() == selected
            and self.logs.setPlainText(output),
        )

    def stop_all(self):
        running = [id for id, _, status in self.containers if _is_running(status)]
        if self._confirm(
            "Stop all workers", f"Stop all {len(running)} running workers?"
        ):
            self._container_action(["stop"], running)

    def remove_all(self):
        ids = [id for id, _, _ in self.containers]
        if self._confirm(
            "Remove all workers",
            f"Remove all {len(ids)} workers? Running ones are stopped first.",
        ):
            self._container_action(["rm", "--force"], ids)

    def _confirm(self, title: str, question: str) -> bool:
        answer = QMessageBox.question(self, title, question)
        return answer == QMessageBox.StandardButton.Yes

    def _container_action(self, args: list[str], ids: list[str]):
        """Runs e.g. `<engine> stop <id>...` on the given containers."""
        if ids:
            self._run([self.engine, *args, *ids], lambda *_: self.refresh())

    def _run(
        self,
        command: list[str],
        on_done: Callable[[int, str], None],
        env: dict[str, str] | None = None,
    ):
        """Runs a command without blocking, then calls `on_done(exit_code, output)`."""
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        if env:
            environment = QProcessEnvironment.systemEnvironment()
            for key, value in env.items():
                environment.insert(key, value)
            process.setProcessEnvironment(environment)

        def finished(exit_code: int, _):
            output = bytes(process.readAllStandardOutput()).decode(errors="replace")
            on_done(exit_code, output)
            process.deleteLater()

        process.finished.connect(finished)
        process.start(command[0], command[1:])


def _is_running(status: str) -> bool:
    """Whether a `podman/docker ps` status (e.g. "Up 3 minutes") is running."""
    return status.startswith("Up")
