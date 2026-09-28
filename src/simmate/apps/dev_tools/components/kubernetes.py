# -*- coding: utf-8 -*-

from simmate.website.htmx.components import HtmxComponent

from ..views import (
    ALL_NAMESPACES,
    _get_kubectl_deployments,
    _get_kubectl_info,
    _run_cmd_full,
)


class KubernetesComponent(HtmxComponent):
    """
    Lists deployments and pods for a selected namespace, with actions to scale
    deployments, plus a log viewer for a selected pod. Every action re-renders
    the whole component.
    """

    template_name = "dev_tools/kubernetes.html"

    namespace: str = "default"
    selected_pod: str = ""
    selected_pod_namespace: str = ""
    log_tail: int = 200
    action_error: str = ""
    action_message: str = ""

    def _clear_messages(self):
        self.action_error = ""
        self.action_message = ""

    def set_namespace(self):
        # str() because post data parsing guesses types (e.g. "123" -> int)
        self.namespace = str(self.form_data.get("namespace") or "default")
        self.selected_pod = ""
        self.selected_pod_namespace = ""
        self._clear_messages()

    def _resolve_deployment(self, deployment: str, namespace: str) -> dict | None:
        """
        Returns the deployment matching the given name + namespace, but only if
        kubectl itself reports it (this also guards against names that could
        be parsed as command-line options).
        """
        deployment, namespace = str(deployment), str(namespace)
        _, deployments = _get_kubectl_deployments(namespace)
        for entry in deployments:
            if entry["name"] == deployment and entry["namespace"] == namespace:
                return entry
        self.action_error = f"Unknown deployment: {namespace}/{deployment}"
        return None

    def scale(self, deployment: str = "", namespace: str = "", replicas: int = 0):
        self._clear_messages()
        entry = self._resolve_deployment(deployment, namespace)
        if not entry:
            return
        replicas = max(int(replicas), 0)
        ok, output = _run_cmd_full(
            [
                "kubectl",
                "scale",
                f"deployment/{entry['name']}",
                "-n",
                entry["namespace"],
                f"--replicas={replicas}",
            ],
            timeout=15,
        )
        if not ok:
            self.action_error = output or "Failed to scale deployment."
            return
        self.action_message = f"Scaled {entry['name']} to {replicas}"

    def show_logs(self, pod: str = "", namespace: str = ""):
        pod, namespace = str(pod), str(namespace)
        if pod == self.selected_pod and namespace == self.selected_pod_namespace:
            self.selected_pod = ""
            self.selected_pod_namespace = ""
        else:
            self.selected_pod = pod
            self.selected_pod_namespace = namespace
            self.log_tail = 200

    def load_more_logs(self):
        self.log_tail += 500

    def refresh(self):
        self._clear_messages()

    def get_context(self):
        ctx = super().get_context()
        kubectl_info = _get_kubectl_info(self.namespace)
        ctx.update(kubectl_info)
        ctx["all_namespaces"] = ALL_NAMESPACES
        ctx["show_namespace"] = self.namespace == ALL_NAMESPACES

        selected = None
        for pod in kubectl_info.get("pods", []):
            if (
                pod["name"] == self.selected_pod
                and pod["namespace"] == self.selected_pod_namespace
            ):
                selected = pod
                break
        if not selected:
            # pod was deleted elsewhere (or nothing is selected)
            self.selected_pod = ""
            self.selected_pod_namespace = ""
            return ctx

        _, logs = _run_cmd_full(
            [
                "kubectl",
                "logs",
                selected["name"],
                "-n",
                selected["namespace"],
                "--tail",
                str(self.log_tail),
                "--timestamps",
                "--all-containers",
            ],
            timeout=10,
            merge_stderr=True,
        )
        ctx["selected"] = selected
        ctx["logs"] = logs
        ctx["has_more_logs"] = len(logs.splitlines()) >= self.log_tail
        return ctx
