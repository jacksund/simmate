# -*- coding: utf-8 -*-

import json
import shutil

from .base import CommandComponent


class DockerComponent(CommandComponent):
    """
    Lists all docker containers (running and stopped) with actions to start,
    stop, and delete them, plus a log viewer for a selected container.
    """

    template_name = "dev_tools/docker.html"

    selected_container: str = ""
    log_tail: int = 200

    def get_containers(self) -> list[dict] | None:
        """
        Returns all containers, or None if the docker daemon can't be reached.
        """
        # -a includes stopped containers, so they can be started or deleted
        result = self.run_command(["docker", "ps", "-a", "--format", "{{json .}}"])
        if result.returncode != 0:
            return None

        containers = []
        for line in result.stdout.splitlines():
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
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
                    "ports": self.format_ports(data.get("Ports", "")),
                }
            )
        return containers

    def _get_container(self, container_id: str) -> dict | None:
        """
        Returns the container with this id, or sets an error if there is none.
        Only ids that docker itself reports are acted on (this also guards
        against ids that could be parsed as command-line options).
        """
        container_id = str(container_id)
        for container in self.get_containers() or []:
            if container["id"] == container_id:
                return container
        self.action_error = f"Unknown container: {container_id}"
        return None

    def _container_action(
        self,
        container_id: str,
        args: list[str],
        verb: str,
        past_tense: str,
        timeout: int,
    ) -> dict | None:
        """
        Runs `docker <args> <id>` and returns the container if it succeeded.
        """
        if not (entry := self._get_container(container_id)):
            return None
        result = self.run_command(["docker", *args, entry["id"]], timeout=timeout)
        succeeded = self.set_action_result(
            result,
            success_message=f"{past_tense} {entry['name']}",
            failure_message=f"Failed to {verb} container.",
        )
        return entry if succeeded else None

    def start(self, container: str = ""):
        self._container_action(container, ["start"], "start", "Started", timeout=15)

    def stop(self, container: str = ""):
        self._container_action(container, ["stop"], "stop", "Stopped", timeout=30)

    def delete(self, container: str = ""):
        entry = self._container_action(
            container, ["rm", "-f"], "delete", "Deleted", timeout=30
        )
        if entry and entry["id"] == self.selected_container:
            self.hide_logs()

    def show_logs(self, container: str = ""):
        container = str(container)
        if container == self.selected_container:
            self.hide_logs()
        else:
            self.selected_container = container
            self.log_tail = 200

    def hide_logs(self):
        self.selected_container = ""

    def load_more_logs(self):
        self.log_tail += 500

    def get_context(self):
        ctx = super().get_context()
        if not shutil.which("docker"):
            self.hide_logs()
            return {**ctx, "available": False}

        containers = self.get_containers()
        if containers is None:
            self.hide_logs()
            ctx.update(
                available=True,
                error="Docker daemon not running",
                containers=[],
            )
            return ctx

        ctx.update(
            available=True,
            error=None,
            containers=containers,
            running_count=sum(c["state"] == "running" for c in containers),
            total_count=len(containers),
        )

        selected = next(
            (c for c in containers if c["id"] == self.selected_container),
            None,
        )
        if not selected:
            # container was deleted elsewhere (or nothing is selected)
            self.hide_logs()
            return ctx

        logs = self.run_command(
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
        ).stdout
        ctx.update(
            selected=selected,
            logs=logs,
            has_more_logs=len(logs.splitlines()) >= self.log_tail,
        )
        return ctx

    def format_ports(self, ports: str | list) -> str:
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
