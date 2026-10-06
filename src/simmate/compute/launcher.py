# -*- coding: utf-8 -*-

"""
Builds the commands that start containerized API workers (via Podman or Docker),
as used by the desktop app.
"""

import shutil
import subprocess

CONTAINER_LABEL = "simmate.worker"
"""
Label on every worker container we start, so they can be found again later.
"""


def find_container_engine() -> str | None:
    """
    The path to podman or docker, if either is installed and running.
    """
    for name in ["podman", "docker"]:
        path = shutil.which(name)
        if not path:
            continue
        try:
            result = subprocess.run([path, "info"], capture_output=True, timeout=15)
        except (subprocess.TimeoutExpired, OSError):
            continue
        if result.returncode == 0:
            return path
    return None


def get_container_env(api_host: str, api_key: str | None) -> dict[str, str]:
    """
    The `SIMMATE__` env vars that point a containerized API worker at `api_host`
    (when any are set, Simmate reads its settings only from the environment).
    """
    # a container's "localhost" is itself, not this machine (e.g. a dev server)
    for localhost in ["localhost", "127.0.0.1"]:
        api_host = api_host.replace(f"//{localhost}", "//host.docker.internal")
    env = {"SIMMATE__CLIENT__HOST": api_host}
    if api_key:
        env["SIMMATE__CLIENT__API_KEY"] = api_key
    return env


def get_container_command(
    engine: str,
    name: str,
    image: str,
    tags: list[str],
    env: dict[str, str],
) -> list[str]:
    """
    The `<engine> run` command for a detached API worker container.

    Only the names of `env` are in the command (`--env KEY`), so the engine reads
    their values from its own environment and secrets never show up in the
    process list. Run this command with `env` set.
    """
    command = [
        engine,
        "run",
        "--detach",
        "--name",
        name,
        "--label",
        CONTAINER_LABEL,
        "--add-host=host.docker.internal:host-gateway",
    ]
    for key in env:
        command += ["--env", key]
    command += [image, "simmate", "compute", "start-worker", "--api"]
    for tag in tags:
        command += ["--tag", tag]
    return command


def get_list_containers_command(engine: str) -> list[str]:
    """
    Lists our worker containers as tab-separated "id, name, status" lines.
    """
    return [
        engine,
        "ps",
        "--all",
        "--filter",
        f"label={CONTAINER_LABEL}",
        "--format",
        "{{.ID}}\t{{.Names}}\t{{.Status}}",
    ]
