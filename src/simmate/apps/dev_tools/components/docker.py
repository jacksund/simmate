# -*- coding: utf-8 -*-

from simmate.website.htmx.components import HtmxComponent

from ..views import _get_docker_info, _run_cmd_full


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
