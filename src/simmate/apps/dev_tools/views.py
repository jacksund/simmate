# -*- coding: utf-8 -*-

import subprocess
from pathlib import Path

from django.shortcuts import render


def _run_cmd(cmd: list[str], timeout: int = 5) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False, ""


def _parse_file_status(status_raw: str) -> tuple[list, list]:
    """Splits `git status --short` output into staged and unstaged file lists."""
    staged = []
    unstaged = []
    for line in status_raw.splitlines():
        if not line.strip():
            continue
        x, y = line[0], line[1]
        path = line[3:].strip()
        p = Path(path)
        parent = p.parent
        dir_str = str(parent) + "/" if str(parent) != "." else ""
        name_str = p.name
        if x not in (" ", "?"):
            staged.append({"status": x, "path": path, "dir": dir_str, "name": name_str})
        if y not in (" ",) or (x == "?" and y == "?"):
            unstaged.append(
                {
                    "status": "??" if x == "?" else y,
                    "path": path,
                    "dir": dir_str,
                    "name": name_str,
                }
            )
    return staged, unstaged


def _get_dirstat() -> list[dict]:
    """Returns top directory change stats from git diff HEAD."""
    _, raw = _run_cmd(["git", "diff", "HEAD", "--dirstat=lines,0"])
    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("%", 1)
        if len(parts) == 2:
            try:
                pct = float(parts[0].strip())
                path = parts[1].strip()
                entries.append({"pct": pct, "path": path})
            except ValueError:
                pass
    return sorted(entries, key=lambda e: e["pct"], reverse=True)[:6]


def _validate_path(file_path: str) -> bool:
    return bool(file_path) and ".." not in file_path and not file_path.startswith("/")


def _get_git_info() -> dict:
    ok, branch = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if not ok:
        return {"available": False}

    _, status_raw = _run_cmd(["git", "status", "--short"])
    _, log_raw = _run_cmd(
        ["git", "log", "--graph", "--oneline", "--all", "--decorate=short", "-20"]
    )
    _, branches_raw = _run_cmd(["git", "branch", "-a"])

    staged, unstaged = _parse_file_status(status_raw)
    log_lines = [line for line in log_raw.splitlines() if line.strip()]
    branches = [b.strip() for b in branches_raw.splitlines() if b.strip()]

    return {
        "available": True,
        "branch": branch,
        "staged_files": staged,
        "unstaged_files": unstaged,
        "log_lines": log_lines,
        "branches": branches,
        "is_clean": not staged and not unstaged,
        "has_staged": bool(staged),
        "dirstat": _get_dirstat(),
    }


def _get_docker_info() -> dict:
    # Check if docker is installed first
    installed, _ = _run_cmd(["docker", "--version"])
    if not installed:
        return {"available": False}

    ok, output = _run_cmd(
        ["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"]
    )
    if not ok:
        return {
            "available": True,
            "error": "Docker daemon not running",
            "containers": [],
        }

    containers = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        containers.append(
            {
                "name": parts[0] if len(parts) > 0 else "",
                "image": parts[1] if len(parts) > 1 else "",
                "status": parts[2] if len(parts) > 2 else "",
                "ports": parts[3] if len(parts) > 3 else "",
            }
        )

    return {"available": True, "containers": containers, "error": None}


def _get_kubectl_info() -> dict:
    # Check if kubectl is installed first
    installed, _ = _run_cmd(["kubectl", "version", "--client", "--output=yaml"])
    if not installed:
        return {"available": False}

    ok, output = _run_cmd(["kubectl", "get", "pods", "-A", "--no-headers"])
    if not ok:
        return {"available": True, "error": "Cannot reach cluster", "pods": []}

    pods = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        pods.append(
            {
                "namespace": parts[0] if len(parts) > 0 else "",
                "name": parts[1] if len(parts) > 1 else "",
                "ready": parts[2] if len(parts) > 2 else "",
                "status": parts[3] if len(parts) > 3 else "",
                "restarts": parts[4] if len(parts) > 4 else "0",
            }
        )

    return {"available": True, "pods": pods, "error": None}


def _parse_diff(diff_text: str) -> list[dict]:
    import re

    rows: list[dict] = []
    old_line = 0
    new_line = 0
    pending_del: list[dict] = []
    pending_add: list[dict] = []

    def flush():
        for i in range(max(len(pending_del), len(pending_add))):
            d = pending_del[i] if i < len(pending_del) else None
            a = pending_add[i] if i < len(pending_add) else None
            rows.append(
                {
                    "type": "row",
                    "left_num": d["num"] if d else "",
                    "left_text": d["text"][1:] if d else "",
                    "left_type": "del" if d else "empty",
                    "right_num": a["num"] if a else "",
                    "right_text": a["text"][1:] if a else "",
                    "right_type": "add" if a else "empty",
                }
            )
        pending_del.clear()
        pending_add.clear()

    for line in diff_text.splitlines():
        if line.startswith(("diff ", "index ", "--- ", "+++ ")):
            flush()
            rows.append({"type": "meta", "text": line})
        elif line.startswith("@@"):
            flush()
            m = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if m:
                old_line = int(m.group(1))
                new_line = int(m.group(2))
            rows.append({"type": "hunk", "text": line})
        elif line.startswith("-"):
            pending_del.append({"num": old_line, "text": line})
            old_line += 1
        elif line.startswith("+"):
            pending_add.append({"num": new_line, "text": line})
            new_line += 1
        else:
            flush()
            content = line[1:] if line.startswith(" ") else line
            rows.append(
                {
                    "type": "row",
                    "left_num": old_line,
                    "left_text": content,
                    "left_type": "ctx",
                    "right_num": new_line,
                    "right_text": content,
                    "right_type": "ctx",
                }
            )
            old_line += 1
            new_line += 1

    flush()
    return rows


def home(request):
    context = {
        "page_title": "Dev Tools",
        "breadcrumbs": ["Apps", "Dev Tools"],
        "git": _get_git_info(),
        "docker": _get_docker_info(),
        "kubectl": _get_kubectl_info(),
    }
    return render(request, "dev_tools/home.html", context)
