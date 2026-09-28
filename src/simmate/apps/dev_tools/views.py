# -*- coding: utf-8 -*-

import json
import re
import shutil
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
        # only strip trailing whitespace -- leading whitespace is meaningful in
        # some outputs (e.g. `git status --short` uses " M" for unstaged edits)
        return result.returncode == 0, result.stdout.rstrip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False, ""


def _run_cmd_full(
    cmd: list[str],
    timeout: int = 5,
    merge_stderr: bool = False,
) -> tuple[bool, str]:
    """
    Like `_run_cmd`, but keeps stderr so error messages can be shown to the
    user. With `merge_stderr`, stdout and stderr are interleaved into a single
    output (e.g. `docker logs` writes a container's stderr to stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT if merge_stderr else subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as error:
        return False, str(error)
    ok = result.returncode == 0
    output = result.stdout or ""
    if not ok and not merge_stderr:
        output = result.stderr or output
    return ok, output.strip()


def _parse_file_status(status_raw: str) -> tuple[list, list]:
    """Splits `git status --short` output into staged and unstaged file lists."""
    staged = []
    unstaged = []
    for line in status_raw.splitlines():
        if not line.strip():
            continue
        x, y = line[0], line[1]
        path = line[3:].strip()
        # renames/copies are reported as "old -> new"
        orig_path = ""
        if " -> " in path:
            orig_path, path = path.split(" -> ", 1)
        p = Path(path)
        parent = p.parent
        dir_str = str(parent) + "/" if str(parent) != "." else ""
        name_str = p.name
        if x not in (" ", "?"):
            staged.append(
                {
                    "status": x,
                    "path": path,
                    "orig_path": orig_path,
                    "dir": dir_str,
                    "name": name_str,
                }
            )
        if y not in (" ",) or (x == "?" and y == "?"):
            unstaged.append(
                {
                    "status": "??" if x == "?" else y,
                    "path": path,
                    "orig_path": "",
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


def _get_rename_source(file_path: str) -> str:
    """
    Returns the original path if `file_path` is the destination of a staged
    rename/copy (otherwise an empty string).
    """
    _, status_raw = _run_cmd(["git", "status", "--short"])
    staged, _ = _parse_file_status(status_raw)
    for entry in staged:
        if entry["path"] == file_path and entry["orig_path"]:
            return entry["orig_path"]
    return ""


def _validate_path(file_path: str) -> bool:
    if not file_path:
        return False
    resolved = (Path.cwd() / file_path).resolve()
    return resolved.is_relative_to(Path.cwd())


def _get_git_info() -> dict:
    ok, branch = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if not ok:
        return {"available": False}

    _, status_raw = _run_cmd(["git", "status", "--short"])
    staged, unstaged = _parse_file_status(status_raw)

    return {
        "available": True,
        "branch": branch,
        "staged_files": staged,
        "unstaged_files": unstaged,
        "is_clean": not staged and not unstaged,
        "has_staged": bool(staged),
        "dirstat": _get_dirstat(),
    }


# -----------------------------------------------------------------------------
# Git log graph
# -----------------------------------------------------------------------------

GRAPH_LANE_W = 14
GRAPH_ROW_H = 28
GRAPH_COLORS = [
    "#f0a30a",  # amber
    "#3b82f6",  # blue
    "#10b981",  # green
    "#ec4899",  # pink
    "#8b5cf6",  # violet
    "#06b6d4",  # cyan
    "#ef4444",  # red
    "#84cc16",  # lime
]


def _parse_refs(refs_raw: str, remotes: tuple[str, ...]) -> list[dict]:
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
            refs.append({"name": ref[8:], "kind": "head", "is_head": True})
        elif ref.startswith("tag: "):
            refs.append({"name": ref[5:], "kind": "tag", "is_head": False})
        elif remotes and ref.startswith(remotes):
            refs.append({"name": ref, "kind": "remote", "is_head": False})
        else:
            refs.append({"name": ref, "kind": "local", "is_head": False})
    return refs


def _get_git_log(limit: int = 50) -> list[dict]:
    """Returns the most recent commits across all refs, in topological order."""
    ok, raw = _run_cmd(
        [
            "git",
            "log",
            "--all",
            "--topo-order",
            f"-n{int(limit)}",
            "--format=%H%x1f%h%x1f%P%x1f%D%x1f%s%x1f%an%x1f%ar%x1e",
        ]
    )
    if not ok:
        return []

    _, remotes_raw = _run_cmd(["git", "remote"])
    remotes = tuple(f"{r}/" for r in remotes_raw.split())

    commits = []
    for record in raw.split("\x1e"):
        fields = record.strip("\n").split("\x1f")
        if len(fields) != 7:
            continue
        full_hash, short_hash, parents, refs, subject, author, age = fields
        commits.append(
            {
                "hash": full_hash,
                "short": short_hash,
                "parents": parents.split(),
                "refs": _parse_refs(refs, remotes) if refs else [],
                # %D always lists HEAD first (either "HEAD -> branch" or a
                # bare "HEAD" when detached)
                "is_head": refs.startswith("HEAD"),
                "subject": subject,
                "author": author,
                "age": age,
            }
        )
    return commits


def _lane_x(lane: int) -> float:
    return lane * GRAPH_LANE_W + GRAPH_LANE_W / 2


def _lane_color(lane: int) -> str:
    return GRAPH_COLORS[lane % len(GRAPH_COLORS)]


def _edge_path(lane_1: int, y_1: float, lane_2: int, y_2: float) -> str:
    x_1 = _lane_x(lane_1)
    x_2 = _lane_x(lane_2)
    if lane_1 == lane_2:
        return f"M {x_1} {y_1} L {x_2} {y_2}"
    y_mid = (y_1 + y_2) / 2
    return f"M {x_1} {y_1} C {x_1} {y_mid}, {x_2} {y_mid}, {x_2} {y_2}"


def _free_slot(lanes: list) -> int:
    """Returns the first empty lane, appending a new one if none are free."""
    for i, lane in enumerate(lanes):
        if lane is None:
            return i
    lanes.append(None)
    return len(lanes) - 1


def _layout_graph(commits: list[dict]) -> int:
    """
    Assigns each commit a lane and builds the SVG paths that connect it to the
    rows above and below (similar to GitKraken's graph). Each commit gets `col`,
    `x`, `color`, `paths`, and `passthrough` keys added in-place.

    Returns the maximum number of lanes used, so that all rows can share the
    same graph width.
    """
    top = 0
    mid = GRAPH_ROW_H / 2
    bottom = GRAPH_ROW_H

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
            col = _free_slot(lanes)
            lanes[col] = commit_hash
        else:
            col = lanes.index(commit_hash)

        # top half: lanes either pass straight through or converge on this node
        for i, expected in enumerate(lanes):
            if expected is None or (is_tip and i == col):
                continue
            if expected == commit_hash:
                paths.append(
                    {"d": _edge_path(i, top, col, mid), "color": _lane_color(i)}
                )
            else:
                paths.append(
                    {"d": _edge_path(i, top, i, bottom), "color": _lane_color(i)}
                )

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
                target = _free_slot(lanes)
                lanes[target] = parent
            paths.append(
                {
                    "d": _edge_path(col, mid, target, bottom),
                    "color": _lane_color(target),
                }
            )

        # trim unused lanes on the right so the graph stays narrow
        while lanes and lanes[-1] is None:
            lanes.pop()

        max_lanes = max(max_lanes, len(lanes), col + 1)
        commit["col"] = col
        commit["x"] = _lane_x(col)
        commit["y"] = mid
        commit["color"] = _lane_color(col)
        commit["paths"] = paths
        # straight lanes used to keep the graph continuous through the
        # expanded commit-details panel below this row
        commit["passthrough"] = [
            {"x": _lane_x(i), "color": _lane_color(i)}
            for i, lane in enumerate(lanes)
            if lane is not None
        ]

    return max_lanes


def _get_branch_refs() -> dict:
    """Returns all local and remote branch names (excluding `*/HEAD`)."""
    _, local_raw = _run_cmd(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads"]
    )
    _, remote_raw = _run_cmd(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/remotes"]
    )
    local = [b for b in local_raw.splitlines() if b.strip()]
    remote = [
        b
        for b in remote_raw.splitlines()
        if b.strip() and not b.endswith("/HEAD") and "/" in b
    ]
    return {"local": local, "remote": remote}


def _get_commit_detail(commit_hash: str) -> dict | None:
    """Returns full metadata and a `--stat` file summary for a single commit."""
    if not re.fullmatch(r"[0-9a-f]{7,40}", commit_hash or ""):
        return None
    ok, raw = _run_cmd(
        [
            "git",
            "show",
            "--stat=80",
            "--format=%H%x1f%an <%ae>%x1f%ad%x1f%B%x1e",
            commit_hash,
        ]
    )
    if not ok or "\x1e" not in raw:
        return None
    header, stat = raw.split("\x1e", 1)
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


def _format_ports(ports: str | list) -> str:
    """
    Docker reports ports as a preformatted string, while podman (and some
    docker-compatible CLIs) give a list of mappings, such as:
        [{'host_ip': '', 'container_port': 5432, 'host_port': 5432,
          'range': 1, 'protocol': 'tcp'}]
    This converts either into docker's style (e.g. "0.0.0.0:5432->5432/tcp").
    """
    if not isinstance(ports, list):
        return str(ports or "")

    formatted = []
    for port in ports:
        if not isinstance(port, dict):
            formatted.append(str(port))
            continue
        container_port = port.get("container_port", "")
        host_port = port.get("host_port", "")
        protocol = port.get("protocol", "tcp")
        size = port.get("range", 1) or 1
        if size > 1 and container_port != "":
            container_port = f"{container_port}-{container_port + size - 1}"
            if host_port != "":
                host_port = f"{host_port}-{host_port + size - 1}"
        if host_port != "":
            host_ip = port.get("host_ip") or "0.0.0.0"
            formatted.append(f"{host_ip}:{host_port}->{container_port}/{protocol}")
        else:
            formatted.append(f"{container_port}/{protocol}")
    return ", ".join(formatted)


def _get_docker_info() -> dict:
    if not shutil.which("docker"):
        return {"available": False}

    # -a includes stopped containers, so they can be started or deleted
    ok, output = _run_cmd(["docker", "ps", "-a", "--format", "{{json .}}"])
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
        try:
            data = json.loads(line)
            # podman uses "Id" and gives names as a list (docker: "ID", str)
            names = data.get("Names", "")
            if isinstance(names, list):
                names = ", ".join(names)
            containers.append(
                {
                    "id": data.get("ID") or data.get("Id", ""),
                    "name": names,
                    "image": data.get("Image", ""),
                    "state": data.get("State", "").lower(),
                    "status": data.get("Status", ""),
                    "created": data.get("RunningFor", ""),
                    "ports": _format_ports(data.get("Ports", "")),
                }
            )
        except json.JSONDecodeError:
            pass

    return {
        "available": True,
        "containers": containers,
        "running_count": sum(c["state"] == "running" for c in containers),
        "total_count": len(containers),
        "error": None,
    }


# sentinel value for the namespace selector that lists every namespace (-A)
ALL_NAMESPACES = "__all__"


def _ns_args(namespace: str) -> list[str]:
    if namespace == ALL_NAMESPACES:
        return ["-A"]
    return ["-n", namespace]


def _get_kubectl_namespaces() -> list[str]:
    ok, output = _run_cmd(["kubectl", "get", "namespaces", "-o", "name"])
    if not ok:
        return []
    return [
        line.strip().removeprefix("namespace/")
        for line in output.splitlines()
        if line.strip()
    ]


def _get_kubectl_pods(namespace: str) -> tuple[bool, list[dict]]:
    ok, output = _run_cmd(
        ["kubectl", "get", "pods", *_ns_args(namespace), "--no-headers"]
    )
    if not ok:
        return False, []

    # the namespace column is only given when listing all namespaces
    offset = 1 if namespace == ALL_NAMESPACES else 0
    pods = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 5 + offset:
            continue
        pods.append(
            {
                "namespace": parts[0] if offset else namespace,
                "name": parts[offset],
                "ready": parts[offset + 1],
                "status": parts[offset + 2],
                # restarts can be followed by "(5m ago)", so age is taken
                # from the end of the line
                "restarts": parts[offset + 3],
                "age": parts[-1],
            }
        )
    return True, pods


def _get_kubectl_deployments(namespace: str) -> tuple[bool, list[dict]]:
    ok, output = _run_cmd(
        ["kubectl", "get", "deployments", *_ns_args(namespace), "-o", "json"],
        timeout=10,
    )
    if not ok:
        return False, []
    try:
        items = json.loads(output).get("items", [])
    except json.JSONDecodeError:
        return False, []

    deployments = []
    for item in items:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        status = item.get("status", {})
        deployments.append(
            {
                "namespace": metadata.get("namespace", ""),
                "name": metadata.get("name", ""),
                "replicas": spec.get("replicas", 0) or 0,
                "ready": status.get("readyReplicas", 0) or 0,
                "up_to_date": status.get("updatedReplicas", 0) or 0,
                "available": status.get("availableReplicas", 0) or 0,
            }
        )
    return True, deployments


def _get_kubectl_info(namespace: str = "default") -> dict:
    if not shutil.which("kubectl"):
        return {"available": False}

    pods_ok, pods = _get_kubectl_pods(namespace)
    if not pods_ok:
        return {
            "available": True,
            "error": "Cannot reach cluster",
            "pods": [],
            "deployments": [],
            "namespaces": [],
        }
    _, deployments = _get_kubectl_deployments(namespace)

    return {
        "available": True,
        "error": None,
        "namespaces": _get_kubectl_namespaces(),
        "pods": pods,
        "deployments": deployments,
        "running_count": sum(p["status"] == "Running" for p in pods),
        "pod_count": len(pods),
    }


def _parse_diff(diff_text: str) -> list[dict]:
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
    }
    return render(request, "dev_tools/home.html", context)
