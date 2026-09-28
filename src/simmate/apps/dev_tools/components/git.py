# -*- coding: utf-8 -*-

import re
from pathlib import Path

from .base import CommandComponent


class GitComponent(CommandComponent):
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

    # Graph rendering configuration
    lane_width: int = 14
    row_height: int = 28
    graph_colors: list[str] = [
        "#f0a30a",  # amber
        "#3b82f6",  # blue
        "#10b981",  # green
        "#ec4899",  # pink
        "#8b5cf6",  # violet
        "#06b6d4",  # cyan
        "#ef4444",  # red
        "#84cc16",  # lime
    ]

    # -------------------------------------------------------------------------
    # Status + diff
    # -------------------------------------------------------------------------

    def validate_path(self, file_path: str) -> bool:
        """Checks that a path is non-empty and stays inside the current directory."""
        if not file_path:
            return False
        resolved = (Path.cwd() / file_path).resolve()
        return resolved.is_relative_to(Path.cwd())

    def get_file_status(self) -> tuple[list[dict], list[dict]]:
        """Returns the (staged, unstaged) files of the working tree."""
        staged = []
        unstaged = []
        result = self.run_command(["git", "status", "--short"])
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            x, y = line[0], line[1]
            path = line[3:].strip()
            # renames/copies are reported as "old -> new"
            orig_path = ""
            if " -> " in path:
                orig_path, path = path.split(" -> ", 1)
            parent = str(Path(path).parent)
            entry = {
                "path": path,
                "orig_path": "",
                "dir": f"{parent}/" if parent != "." else "",
                "name": Path(path).name,
            }
            if x == "?":
                unstaged.append({**entry, "status": "??"})
                continue
            if x != " ":
                staged.append({**entry, "status": x, "orig_path": orig_path})
            if y != " ":
                unstaged.append({**entry, "status": y})
        return staged, unstaged

    def get_dirstat(self) -> list[dict]:
        """Returns the top directories changed since HEAD."""
        result = self.run_command(["git", "diff", "HEAD", "--dirstat=lines,0"])
        entries = []
        for line in result.stdout.splitlines():
            pct, sep, path = line.strip().partition("%")
            if not sep:
                continue
            try:
                entries.append({"pct": float(pct.strip()), "path": path.strip()})
            except ValueError:
                pass
        return sorted(entries, key=lambda e: e["pct"], reverse=True)[:6]

    def _pathspecs(self, file_path: str, staged: list[dict] | None = None) -> list[str]:
        """
        Returns the pathspecs needed for git commands on `file_path`. For a staged
        rename, both the old and new paths are needed so git can pair them
        (otherwise it only sees an added file, or nothing at all).
        """
        if staged is None:
            staged, _ = self.get_file_status()
        for entry in staged:
            if entry["path"] == file_path and entry["orig_path"]:
                return [entry["orig_path"], file_path]
        return [file_path]

    def _diff_row(self, left: dict | None, right: dict | None) -> dict:
        return {
            "type": "row",
            "left_num": left["num"] if left else "",
            "left_text": left["text"] if left else "",
            "left_type": left["type"] if left else "empty",
            "right_num": right["num"] if right else "",
            "right_text": right["text"] if right else "",
            "right_type": right["type"] if right else "empty",
        }

    def parse_diff(self, diff_text: str) -> list[dict]:
        """
        Converts unified diff output into side-by-side rows. Consecutive removed
        and added lines are paired up so that edits line up next to each other.
        """
        rows: list[dict] = []
        old_line = 0
        new_line = 0
        pending_del: list[dict] = []
        pending_add: list[dict] = []

        def flush():
            for i in range(max(len(pending_del), len(pending_add))):
                rows.append(
                    self._diff_row(
                        pending_del[i] if i < len(pending_del) else None,
                        pending_add[i] if i < len(pending_add) else None,
                    )
                )
            pending_del.clear()
            pending_add.clear()

        for line in diff_text.splitlines():
            if line.startswith(("diff ", "index ", "--- ", "+++ ")):
                # file headers are already shown above the diff
                flush()
            elif line.startswith("@@"):
                flush()
                match = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    old_line = int(match.group(1))
                    new_line = int(match.group(2))
                rows.append({"type": "hunk", "text": line})
            elif line.startswith("-"):
                pending_del.append({"num": old_line, "text": line[1:], "type": "del"})
                old_line += 1
            elif line.startswith("+"):
                pending_add.append({"num": new_line, "text": line[1:], "type": "add"})
                new_line += 1
            else:
                flush()
                content = line[1:] if line.startswith(" ") else line
                rows.append(
                    self._diff_row(
                        {"num": old_line, "text": content, "type": "ctx"},
                        {"num": new_line, "text": content, "type": "ctx"},
                    )
                )
                old_line += 1
                new_line += 1

        flush()
        return rows

    def get_diff_context(self, staged: list[dict], unstaged: list[dict]) -> dict:
        """
        Builds the side-by-side diff for the selected file, plus which
        stage/unstage button to show.
        """
        file_path = self.selected_file
        view = self.selected_view
        is_staged = any(f["path"] == file_path for f in staged)
        unstaged_entry = next((f for f in unstaged if f["path"] == file_path), None)
        is_untracked = bool(unstaged_entry) and unstaged_entry["status"] == "??"

        cached_cmd = [
            "git",
            "diff",
            "--cached",
            "-M",
            "--",
            *self._pathspecs(file_path, staged),
        ]
        if view == "staged" and is_staged:
            diff_text = self.run_command(cached_cmd).stdout
        elif is_untracked:
            # (exits with 1 when there are differences, so returncode is ignored)
            diff_text = self.run_command(
                ["git", "diff", "--no-index", "/dev/null", file_path]
            ).stdout
        else:
            diff_text = self.run_command(["git", "diff", "--", file_path]).stdout
            if not diff_text and is_staged:
                diff_text = self.run_command(cached_cmd).stdout

        return {
            "diff_lines": self.parse_diff(diff_text),
            "show_stage_btn": view == "unstaged" and bool(unstaged_entry),
            "show_unstage_btn": view == "staged" and is_staged,
        }

    def show_diff(self, file: str = "", view: str = "unstaged"):
        file = str(file)
        if self.validate_path(file):
            self.selected_file = file
            self.selected_view = view

    def stage_file(self, file: str = ""):
        path = str(file or self.selected_file)
        if self.validate_path(path):
            self.run_command(["git", "add", "--", *self._pathspecs(path)])
            self.selected_file = path
            self.selected_view = "staged"
        self.commit_error = ""

    def unstage_file(self, file: str = ""):
        path = str(file or self.selected_file)
        if self.validate_path(path):
            self.run_command(
                ["git", "restore", "--staged", "--", *self._pathspecs(path)]
            )
            self.selected_file = path
            self.selected_view = "unstaged"
        self.commit_error = ""

    def stage_all(self):
        self.run_command(["git", "add", "-A"])
        self.selected_file = ""
        self.commit_error = ""

    def unstage_all(self):
        self.run_command(["git", "restore", "--staged", "."])
        self.selected_file = ""
        self.commit_error = ""

    def commit(self):
        message = self.form_data.get("commit_message", "").strip()
        if not message:
            self.commit_error = "Commit message cannot be empty."
            return
        result = self.run_command(["git", "commit", "-m", message], timeout=15)
        if result.returncode != 0:
            self.commit_error = (
                result.stderr or result.stdout
            ).strip() or "Commit failed."
            return
        self.form_data["commit_message"] = ""
        self.selected_file = ""
        self.commit_error = ""

    def lint(self):
        result = self.run_command(["simmate", "dev", "lint"], timeout=60)
        output = (result.stdout or result.stderr).strip()
        self.lint_output = output or (
            "No issues found."
            if result.returncode == 0
            else "Lint failed with no output."
        )
        self.lint_error = result.returncode != 0
        self.selected_file = ""

    # -------------------------------------------------------------------------
    # Log + branches
    # -------------------------------------------------------------------------

    def parse_refs(self, refs_raw: str, remotes: tuple[str, ...]) -> list[dict]:
        """
        Converts `%D` output (e.g. "HEAD -> main, origin/main, tag: v1.0") into a
        list of ref dicts with a `kind` of head, local, remote, or tag. `remotes`
        are remote-name prefixes such as ("origin/",).
        """
        refs = []
        for ref in refs_raw.split(", "):
            ref = ref.strip()
            if not ref or ref == "HEAD" or ref.endswith("/HEAD"):
                continue
            if ref.startswith("HEAD -> "):
                name, kind = ref.removeprefix("HEAD -> "), "head"
            elif ref.startswith("tag: "):
                name, kind = ref.removeprefix("tag: "), "tag"
            elif remotes and ref.startswith(remotes):
                name, kind = ref, "remote"
            else:
                name, kind = ref, "local"
            refs.append({"name": name, "kind": kind, "is_head": kind == "head"})
        return refs

    def get_log(self) -> list[dict]:
        """Returns the most recent commits across all refs, in topological order."""
        result = self.run_command(
            [
                "git",
                "log",
                "--all",
                "--topo-order",
                f"-n{int(self.log_limit)}",
                "--format=%H%x1f%h%x1f%P%x1f%D%x1f%s%x1f%an%x1f%ar%x1e",
            ]
        )
        if result.returncode != 0:
            return []

        remotes = tuple(
            f"{r}/" for r in self.run_command(["git", "remote"]).stdout.split()
        )

        commits = []
        for record in result.stdout.split("\x1e"):
            fields = record.strip("\n").split("\x1f")
            if len(fields) != 7:
                continue
            full_hash, short_hash, parents, refs, subject, author, age = fields
            commits.append(
                {
                    "hash": full_hash,
                    "short": short_hash,
                    "parents": parents.split(),
                    "refs": self.parse_refs(refs, remotes),
                    # %D always lists HEAD first (either "HEAD -> branch" or a
                    # bare "HEAD" when detached)
                    "is_head": refs.startswith("HEAD"),
                    "subject": subject,
                    "author": author,
                    "age": age,
                }
            )
        return commits

    def get_branches(self) -> dict:
        """Returns all local and remote branch names (excluding `*/HEAD`)."""
        list_cmd = ["git", "for-each-ref", "--format=%(refname:short)"]
        local_raw = self.run_command([*list_cmd, "refs/heads"]).stdout
        remote_raw = self.run_command([*list_cmd, "refs/remotes"]).stdout
        local = [b for b in local_raw.splitlines() if b.strip()]
        remote = [
            b
            for b in remote_raw.splitlines()
            if b.strip() and not b.endswith("/HEAD") and "/" in b
        ]
        return {"local": local, "remote": remote}

    def get_commit_detail(self) -> dict | None:
        """Returns full metadata and a `--stat` summary for the selected commit."""
        if not re.fullmatch(r"[0-9a-f]{7,40}", self.selected_commit):
            return None
        result = self.run_command(
            [
                "git",
                "show",
                "--stat=80",
                "--format=%H%x1f%an <%ae>%x1f%ad%x1f%B%x1e",
                self.selected_commit,
            ]
        )
        if result.returncode != 0 or "\x1e" not in result.stdout:
            return None
        header, stat = result.stdout.split("\x1e", 1)
        fields = header.split("\x1f")
        if len(fields) != 4:
            return None
        full_hash, author, date, body = fields
        return {
            "hash": full_hash,
            "author": author,
            "date": date,
            "body": body.strip(),
            "stat_lines": [line for line in stat.splitlines() if line.strip()],
        }

    def load_more(self):
        self.log_limit += 50

    def select_commit(self, commit: str = ""):
        commit = str(commit)
        self.selected_commit = "" if commit == self.selected_commit else commit

    def checkout(self, branch: str = ""):
        branch = str(branch)
        branches = self.get_branches()

        # only allow names that git itself reports (this also guards against
        # names that could be parsed as command-line options)
        if branch in branches["local"]:
            cmd = ["git", "switch", branch]
        elif branch in branches["remote"]:
            local_name = branch.split("/", 1)[1]
            if local_name in branches["local"]:
                cmd = ["git", "switch", local_name]
            else:
                cmd = ["git", "switch", "--track", branch]
        else:
            self.action_error = f"Unknown branch: {branch}"
            return

        result = self.run_command(cmd, timeout=15)
        # git reports checkout progress on stderr, even on success
        if self.set_action_result(
            result,
            success_message=result.stderr.strip() or f"Switched to {branch}",
            failure_message="Checkout failed.",
        ):
            # the working tree may have changed, so reset any file-specific views
            self.selected_file = ""
            self.selected_commit = ""

    def fetch(self):
        result = self.run_command(["git", "fetch", "--all", "--prune"], timeout=30)
        # git reports fetch progress on stderr, even on success
        self.set_action_result(
            result,
            success_message=result.stderr.strip() or "Already up to date.",
            failure_message="Fetch failed.",
        )

    # -------------------------------------------------------------------------
    # Commit graph layout
    # -------------------------------------------------------------------------

    def _lane_x(self, lane: int) -> float:
        return lane * self.lane_width + self.lane_width / 2

    def _lane_color(self, lane: int) -> str:
        return self.graph_colors[lane % len(self.graph_colors)]

    def _edge_path(self, lane_1: int, y_1: float, lane_2: int, y_2: float) -> str:
        x_1 = self._lane_x(lane_1)
        x_2 = self._lane_x(lane_2)
        if lane_1 == lane_2:
            return f"M {x_1} {y_1} L {x_2} {y_2}"
        y_mid = (y_1 + y_2) / 2
        return f"M {x_1} {y_1} C {x_1} {y_mid}, {x_2} {y_mid}, {x_2} {y_2}"

    def _free_slot(self, lanes: list) -> int:
        """Returns the first empty lane, appending a new one if none are free."""
        for i, lane in enumerate(lanes):
            if lane is None:
                return i
        lanes.append(None)
        return len(lanes) - 1

    def layout_graph(self, commits: list[dict]) -> int:
        """
        Assigns each commit a lane and builds the SVG paths that connect it to the
        rows above and below. Each commit gets `col`, `x`, `y`, `color`, `paths`,
        and `passthrough` keys added in-place.

        Returns the maximum number of lanes used, so that all rows can share the
        same graph width.
        """
        top = 0
        mid = self.row_height / 2
        bottom = self.row_height

        # each lane holds the hash of the commit it expects next (or None if free)
        lanes: list[str | None] = []
        max_lanes = 1

        for commit in commits:
            commit_hash = commit["hash"]
            paths = []

            # find this commit's lane, or claim a new one (i.e. a branch tip, which
            # has nothing drawn above it)
            is_tip = commit_hash not in lanes
            if is_tip:
                col = self._free_slot(lanes)
                lanes[col] = commit_hash
            else:
                col = lanes.index(commit_hash)

            # top half: lanes either converge on this node or pass straight through
            for i, expected in enumerate(lanes):
                if expected is None or (is_tip and i == col):
                    continue
                if expected == commit_hash:
                    d = self._edge_path(i, top, col, mid)
                else:
                    d = self._edge_path(i, top, i, bottom)
                paths.append({"d": d, "color": self._lane_color(i)})

            # bottom half: free every lane that pointed at this commit, then route
            # the parents into lanes
            lanes = [None if lane == commit_hash else lane for lane in lanes]
            for n, parent in enumerate(commit["parents"]):
                if n == 0 and parent not in lanes:
                    lanes[col] = parent
                    target = col
                elif parent in lanes:
                    target = lanes.index(parent)
                else:
                    target = self._free_slot(lanes)
                    lanes[target] = parent
                paths.append(
                    {
                        "d": self._edge_path(col, mid, target, bottom),
                        "color": self._lane_color(target),
                    }
                )

            # trim unused lanes on the right so the graph stays narrow
            while lanes and lanes[-1] is None:
                lanes.pop()

            max_lanes = max(max_lanes, len(lanes), col + 1)
            commit["col"] = col
            commit["x"] = self._lane_x(col)
            commit["y"] = mid
            commit["color"] = self._lane_color(col)
            commit["paths"] = paths
            # straight lanes used to keep the graph continuous through the
            # expanded commit-details panel below this row
            commit["passthrough"] = [
                {"x": self._lane_x(i), "color": self._lane_color(i)}
                for i, lane in enumerate(lanes)
                if lane is not None
            ]

        return max_lanes

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_context(self):
        ctx = super().get_context()
        head = self.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if head.returncode != 0:
            return {**ctx, "available": False}

        staged, unstaged = self.get_file_status()
        commits = self.get_log()
        max_lanes = self.layout_graph(commits)
        ctx.update(
            available=True,
            branch=head.stdout.strip(),
            # status panel
            staged_files=staged,
            unstaged_files=unstaged,
            is_clean=not staged and not unstaged,
            has_staged=bool(staged),
            dirstat=self.get_dirstat(),
            # log panel
            commits=commits,
            has_more_commits=len(commits) >= self.log_limit,
            graph_width=max_lanes * self.lane_width,
            row_h=self.row_height,
            branches=self.get_branches(),
            commit_detail=self.get_commit_detail() if self.selected_commit else None,
        )
        if self.selected_file:
            ctx.update(self.get_diff_context(staged, unstaged))
        return ctx
