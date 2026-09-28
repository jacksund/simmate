# -*- coding: utf-8 -*-

import json
import shutil

from .base import CommandComponent


class KubernetesComponent(CommandComponent):
    """
    Lists deployments and pods for a selected namespace, with actions to scale
    deployments, plus a log viewer for a selected pod.
    """

    template_name = "dev_tools/kubernetes.html"

    # sentinel value for the namespace selector that lists every namespace (-A)
    all_namespaces: str = "__all__"

    namespace: str = "default"
    selected_pod: str = ""
    selected_pod_namespace: str = ""
    log_tail: int = 200

    def _namespace_args(self, namespace: str) -> list[str]:
        return ["-A"] if namespace == self.all_namespaces else ["-n", namespace]

    def get_namespaces(self) -> list[str]:
        result = self.run_command(["kubectl", "get", "namespaces", "-o", "name"])
        if result.returncode != 0:
            return []
        return [
            line.strip().removeprefix("namespace/")
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    def get_pods(self, namespace: str) -> list[dict] | None:
        """Returns the pods in a namespace, or None if the cluster is unreachable."""
        result = self.run_command(
            ["kubectl", "get", "pods", *self._namespace_args(namespace), "--no-headers"]
        )
        if result.returncode != 0:
            return None

        # the namespace column is only given when listing all namespaces
        offset = 1 if namespace == self.all_namespaces else 0
        pods = []
        for line in result.stdout.splitlines():
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
        return pods

    def get_deployments(self, namespace: str) -> list[dict]:
        result = self.run_command(
            [
                "kubectl",
                "get",
                "deployments",
                *self._namespace_args(namespace),
                "-o",
                "json",
            ],
            timeout=10,
        )
        if result.returncode != 0:
            return []
        try:
            items = json.loads(result.stdout).get("items", [])
        except json.JSONDecodeError:
            return []

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
        return deployments

    def set_namespace(self):
        # str() because post data parsing guesses types (e.g. "123" -> int)
        self.namespace = str(self.form_data.get("namespace") or "default")
        self.hide_logs()

    def scale(self, deployment: str = "", namespace: str = "", replicas: int = 0):

        # only allow names that kubectl itself reports (this also guards
        # against names that could be parsed as command-line options)
        deployment, namespace = str(deployment), str(namespace)
        entry = next(
            (
                d
                for d in self.get_deployments(namespace)
                if d["name"] == deployment and d["namespace"] == namespace
            ),
            None,
        )
        if not entry:
            self.action_error = f"Unknown deployment: {namespace}/{deployment}"
            return

        replicas = max(int(replicas), 0)
        result = self.run_command(
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
        self.set_action_result(
            result,
            success_message=f"Scaled {entry['name']} to {replicas}",
            failure_message="Failed to scale deployment.",
        )

    def show_logs(self, pod: str = "", namespace: str = ""):
        pod, namespace = str(pod), str(namespace)
        if pod == self.selected_pod and namespace == self.selected_pod_namespace:
            self.hide_logs()
        else:
            self.selected_pod = pod
            self.selected_pod_namespace = namespace
            self.log_tail = 200

    def hide_logs(self):
        self.selected_pod = ""
        self.selected_pod_namespace = ""

    def load_more_logs(self):
        self.log_tail += 500

    def get_context(self):
        ctx = super().get_context()
        ctx.update(
            all_namespaces=self.all_namespaces,
            show_namespace=self.namespace == self.all_namespaces,
        )
        if not shutil.which("kubectl"):
            self.hide_logs()
            return {**ctx, "available": False}

        pods = self.get_pods(self.namespace)
        if pods is None:
            self.hide_logs()
            ctx.update(
                available=True,
                error="Cannot reach cluster",
                pods=[],
                deployments=[],
                namespaces=[],
            )
            return ctx

        ctx.update(
            available=True,
            error=None,
            namespaces=self.get_namespaces(),
            pods=pods,
            deployments=self.get_deployments(self.namespace),
            running_count=sum(p["status"] == "Running" for p in pods),
            pod_count=len(pods),
        )

        selected = next(
            (
                pod
                for pod in pods
                if pod["name"] == self.selected_pod
                and pod["namespace"] == self.selected_pod_namespace
            ),
            None,
        )
        if not selected:
            # pod was deleted elsewhere (or nothing is selected)
            self.hide_logs()
            return ctx

        logs = self.run_command(
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
        ).stdout
        ctx.update(
            selected=selected,
            logs=logs,
            has_more_logs=len(logs.splitlines()) >= self.log_tail,
        )
        return ctx
