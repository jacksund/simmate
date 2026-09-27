# -*- coding: utf-8 -*-

from django.http import HttpResponse

from simmate.website.htmx.components import HtmxComponent

from .views import (
    _get_git_info,
    _parse_diff,
    _run_cmd,
    _validate_path,
)


class GitStatusComponent(HtmxComponent):

    template_name = "dev_tools/git_status.html"

    selected_file: str = ""
    selected_view: str = "unstaged"
    commit_error: str = ""
    lint_output: str = ""
    lint_error: bool = False

    def show_diff(self, file: str = "", view: str = "unstaged"):
        if _validate_path(file):
            self.selected_file = file
            self.selected_view = view

    def stage_file(self, file: str = ""):
        target = file or self.selected_file
        if target and _validate_path(target):
            _run_cmd(["git", "add", "--", target])
            self.selected_file = target
            self.selected_view = "staged"
        self.commit_error = ""

    def unstage_file(self, file: str = ""):
        target = file or self.selected_file
        if target and _validate_path(target):
            _run_cmd(["git", "restore", "--staged", "--", target])
            self.selected_file = target
            self.selected_view = "unstaged"
        self.commit_error = ""

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
        self.selected_file = ""
        self.commit_error = ""
        response = HttpResponse()
        response["HX-Refresh"] = "true"
        return response

    def refresh(self):
        pass

    def lint(self):
        ok, output = _run_cmd(["simmate", "dev", "lint"], timeout=60)
        self.lint_output = output or (
            "No issues found." if ok else "Lint failed with no output."
        )
        self.lint_error = not ok
        self.selected_file = ""

    def get_context(self):
        ctx = super().get_context()
        git_info = _get_git_info()
        ctx.update(git_info)

        diff_lines = []
        show_stage_btn = False
        show_unstage_btn = False
        if self.selected_file and git_info.get("available"):
            diff_lines, show_stage_btn, show_unstage_btn = self._get_diff_context()

        ctx["diff_lines"] = diff_lines
        ctx["show_stage_btn"] = show_stage_btn
        ctx["show_unstage_btn"] = show_unstage_btn
        ctx["lint_output"] = self.lint_output
        ctx["lint_error"] = self.lint_error
        return ctx

    def _get_diff_context(self) -> tuple[list, bool, bool]:
        file_path = self.selected_file
        view = self.selected_view

        _, status_raw = _run_cmd(["git", "status", "--short", "--", file_path])
        is_staged = False
        is_untracked = False
        is_unstaged = False
        if status_raw.strip():
            x, y = status_raw[0], status_raw[1]
            is_staged = x not in (" ", "?")
            is_untracked = x == "?" and y == "?"
            is_unstaged = y not in (" ",) and not is_untracked

        if view == "staged" and is_staged:
            _, diff_text = _run_cmd(["git", "diff", "--cached", "--", file_path])
        elif is_untracked:
            _, diff_text = _run_cmd(
                ["git", "diff", "--no-index", "/dev/null", file_path]
            )
        else:
            _, diff_text = _run_cmd(["git", "diff", "--", file_path])
            if not diff_text and is_staged:
                _, diff_text = _run_cmd(["git", "diff", "--cached", "--", file_path])

        show_stage_btn = view == "unstaged" and (is_unstaged or is_untracked)
        show_unstage_btn = view == "staged" and is_staged

        return _parse_diff(diff_text), show_stage_btn, show_unstage_btn
