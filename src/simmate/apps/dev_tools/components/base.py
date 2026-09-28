# -*- coding: utf-8 -*-

import subprocess

from simmate.website.htmx.components import HtmxComponent


class CommandComponent(HtmxComponent):
    """
    Base for components that shell out to a CLI (git, docker, kubectl, etc.).
    """

    def run_command(
        self,
        cmd: list[str],
        timeout: int = 10,
        merge_stderr: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Runs a command and captures its output safely.
        """
        try:
            return subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT if merge_stderr else subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as error:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr=str(error),
            )

    def set_action_result(
        self,
        result: subprocess.CompletedProcess,
        success_message: str,
        failure_message: str,
    ) -> bool:
        """
        Sets `action_message` or `action_error` from a command's result and
        returns whether the command succeeded.
        """
        if result.returncode == 0:
            self.action_message = success_message
            return True
        self.action_error = (result.stderr or result.stdout).strip() or failure_message
        return False
