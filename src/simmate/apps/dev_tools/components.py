# -*- coding: utf-8 -*-

import subprocess

from simmate.website.htmx.components import HtmxComponent

from .views import (
    GRAPH_LANE_W,
    GRAPH_ROW_H,
    _get_branch_refs,
    _get_commit_detail,
    _get_docker_info,
    _get_git_info,
    _get_git_log,
    _get_rename_source,
    _layout_graph,
    _parse_diff,
    _run_cmd,
    _run_cmd_full,
    _validate_path,
)


class DockerComponent(HtmxComponent):
    """
    Lists all docker containers (running and stopped) with actions to start,
    stop, and delete them, plus a log viewer for a selected container. Every
    action re-renders the whole component.
    """

    template_name = "dev_tools/docker.html"

    selected_container: str = ""
    log_tail: int = 200
    action_error: str = ""
    action_message: str = ""

    def _clear_messages(self):
        self.action_error = ""
        self.action_message = ""

    def _resolve(self, container: str) -> dict | None:
        """
        Returns the container matching the given id, but only if docker itself
        reports it (this also guards against ids that could be parsed as
        command-line options).
        """
        container = str(container)
        for entry in _get_docker_info().get("containers", []):
            if container and entry["id"] == container:
                return entry
        self.action_error = f"Unknown container: {container}"
        return None

    def _run_action(
        self,
        container: str,
        docker_cmd: list[str],
        verb: str,
        timeout: int = 15,
    ) -> bool:
        self._clear_messages()
        entry = self._resolve(container)
        if not entry:
            return False
        ok, output = _run_cmd_full(
            ["docker", *docker_cmd, entry["id"]],
            timeout=timeout,
        )
        if not ok:
            self.action_error = output or f"Failed to {verb.lower()} container."
            return False
        self.action_message = f"{verb} {entry['name']}"
        return True

    def start(self, container: str = ""):
        self._run_action(container, ["start"], "Started")

    def stop(self, container: str = ""):
        self._run_action(container, ["stop"], "Stopped", timeout=30)

    def delete(self, container: str = ""):
        if self._run_action(container, ["rm", "-f"], "Deleted", timeout=30):
            if str(container) == self.selected_container:
                self.selected_container = ""

    def show_logs(self, container: str = ""):
        container = str(container)
        if container == self.selected_container:
            self.selected_container = ""
        else:
            self.selected_container = container
            self.log_tail = 200

    def load_more_logs(self):
        self.log_tail += 500

    def refresh(self):
        self._clear_messages()

    def get_context(self):
        ctx = super().get_context()
        docker_info = _get_docker_info()
        ctx.update(docker_info)

        selected = None
        for entry in docker_info.get("containers", []):
            if entry["id"] == self.selected_container:
                selected = entry
                break
        if not selected:
            # container was deleted elsewhere (or nothing is selected)
            self.selected_container = ""
            return ctx

        _, logs = _run_cmd_full(
            [
                "docker",
                "logs",
                "--tail",
                str(self.log_tail),
                "--timestamps",
                selected["id"],
            ],
            timeout=10,
            merge_stderr=True,
        )
        ctx["selected"] = selected
        ctx["logs"] = logs
        ctx["has_more_logs"] = len(logs.splitlines()) >= self.log_tail
        return ctx


class GitComponent(HtmxComponent):
    """
    A combined git panel: commit graph (log + branches), working tree status
    (staged/unstaged files + commit box), and a diff viewer. Every action
    re-renders the whole component, so all panels always stay in sync.
    """

    template_name = "dev_tools/git.html"

    # status + diff state
    selected_file: str = ""
    selected_view: str = "unstaged"
    commit_error: str = ""
    lint_output: str = ""
    lint_error: bool = False

    # log state
    log_limit: int = 50
    selected_commit: str = ""
    action_error: str = ""
    action_message: str = ""

    # -------------------------------------------------------------------------
    # Status + diff actions
    # -------------------------------------------------------------------------

    def show_diff(self, file: str = "", view: str = "unstaged"):
        if _validate_path(file):
            self.selected_file = file
            self.selected_view = view

    def _toggle_file_stage(self, file: str, git_cmd: list[str], view: str):
        target = file or self.selected_file
        if target and _validate_path(target):
            _run_cmd(git_cmd + ["--"] + self._with_rename_source(target))
            self.selected_file = target
            self.selected_view = view
        self.commit_error = ""

    def stage_file(self, file: str = ""):
        self._toggle_file_stage(file, ["git", "add"], "staged")

    def unstage_file(self, file: str = ""):
        self._toggle_file_stage(file, ["git", "restore", "--staged"], "unstaged")

    def stage_all(self):
        _run_cmd(["git", "add", "-A"])
        self.selected_file = ""
        self.commit_error = ""

    def unstage_all(self):
        _run_cmd(["git", "restore", "--staged", "."])
        self.selected_file = ""
        self.commit_error = ""

    def commit(self):
        message = self.form_data.get("commit_message", "").strip()
        if not message:
            self.commit_error = "Commit message cannot be empty."
            return
        ok, output = _run_cmd(["git", "commit", "-m", message], timeout=15)
        if not ok:
            self.commit_error = output or "Commit failed."
            return
        self.form_data["commit_message"] = ""
        self.selected_file = ""
        self.commit_error = ""

    def refresh(self):
        self._clear_messages()

    def lint(self):
        ok, output = _run_cmd(["simmate", "dev", "lint"], timeout=60)
        self.lint_output = output or (
            "No issues found." if ok else "Lint failed with no output."
        )
        self.lint_error = not ok
        self.selected_file = ""

    # -------------------------------------------------------------------------
    # Log + branch actions
    # -------------------------------------------------------------------------

    def _clear_messages(self):
        self.action_error = ""
        self.action_message = ""

    def load_more(self):
        self.log_limit += 50

    def select_commit(self, commit: str = ""):
        commit = str(commit)
        self.selected_commit = "" if commit == self.selected_commit else commit

    def checkout(self, branch: str = ""):
        self._clear_messages()
        branch = str(branch)
        refs = _get_branch_refs()

        # only allow names that git itself reports (this also guards against
        # names that could be parsed as command-line options)
        if branch in refs["local"]:
            cmd = ["git", "switch", branch]
        elif branch in refs["remote"]:
            local_name = branch.split("/", 1)[1]
            if local_name in refs["local"]:
                cmd = ["git", "switch", local_name]
            else:
                cmd = ["git", "switch", "--track", branch]
        else:
            self.action_error = f"Unknown branch: {branch}"
            return

        # git writes checkout errors to stderr, so we can't use _run_cmd here
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        except (subprocess.TimeoutExpired, OSError) as error:
            self.action_error = str(error)
            return
        if result.returncode != 0:
            self.action_error = (result.stderr or result.stdout).strip() or (
                "Checkout failed."
            )
            return

        # the working tree may have changed, so reset any file-specific views
        self.selected_file = ""
        self.selected_commit = ""
        self.action_message = result.stderr.strip() or f"Switched to {branch}"

    def fetch(self):
        self._clear_messages()
        try:
            result = subprocess.run(
                ["git", "fetch", "--all", "--prune"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, OSError) as error:
            self.action_error = str(error)
            return
        if result.returncode != 0:
            self.action_error = result.stderr.strip() or "Fetch failed."
        else:
            # git fetch reports progress on stderr, even on success
            self.action_message = result.stderr.strip() or "Already up to date."

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_context(self):
        ctx = super().get_context()
        git_info = _get_git_info()
        ctx.update(git_info)
        if not git_info.get("available"):
            return ctx

        # log panel
        commits = _get_git_log(self.log_limit)
        max_lanes = _layout_graph(commits)
        ctx.update(
            {
                "commits": commits,
                "has_more_commits": len(commits) >= self.log_limit,
                "graph_width": max_lanes * GRAPH_LANE_W,
                "row_h": GRAPH_ROW_H,
                "branches": _get_branch_refs(),
                "commit_detail": (
                    _get_commit_detail(self.selected_commit)
                    if self.selected_commit
                    else None
                ),
            }
        )

        # diff panel
        diff_lines = []
        show_stage_btn = False
        show_unstage_btn = False
        if self.selected_file:
            diff_lines, show_stage_btn, show_unstage_btn = self._get_diff_context()
        ctx["diff_lines"] = diff_lines
        ctx["show_stage_btn"] = show_stage_btn
        ctx["show_unstage_btn"] = show_unstage_btn
        ctx["lint_output"] = self.lint_output
        ctx["lint_error"] = self.lint_error
        return ctx

    @staticmethod
    def _with_rename_source(file_path: str) -> list[str]:
        """
        Returns the pathspecs needed for git commands on `file_path`. For a
        staged rename, both the old and new paths are needed so git can pair
        them (otherwise it only sees an added file, or nothing at all).
        """
        orig_path = _get_rename_source(file_path)
        return [orig_path, file_path] if orig_path else [file_path]

    def _get_diff_context(self) -> tuple[list, bool, bool]:
        file_path = self.selected_file
        view = self.selected_view
        paths = self._with_rename_source(file_path)

        _, status_raw = _run_cmd(["git", "status", "--short", "--", *paths])
        is_staged = False
        is_untracked = False
        is_unstaged = False
        if status_raw.strip():
            x, y = status_raw[0], status_raw[1]
            is_staged = x not in (" ", "?")
            is_untracked = x == "?" and y == "?"
            is_unstaged = y not in (" ",) and not is_untracked

        if view == "staged" and is_staged:
            _, diff_text = _run_cmd(["git", "diff", "--cached", "-M", "--", *paths])
        elif is_untracked:
            _, diff_text = _run_cmd(
                ["git", "diff", "--no-index", "/dev/null", file_path]
            )
        else:
            _, diff_text = _run_cmd(["git", "diff", "--", file_path])
            if not diff_text and is_staged:
                _, diff_text = _run_cmd(["git", "diff", "--cached", "-M", "--", *paths])

        show_stage_btn = view == "unstaged" and (is_unstaged or is_untracked)
        show_unstage_btn = view == "staged" and is_staged

        return _parse_diff(diff_text), show_stage_btn, show_unstage_btn
