# -*- coding: utf-8 -*-

"""
This defines commands for managing local Kubernetes/Helm deployments. All commands are
accessible through the `simmate dev k8s` command.
"""

import logging
import subprocess

import typer

k8s_app = typer.Typer(rich_markup_mode="markdown")


@k8s_app.callback(no_args_is_help=True)
def k8s():
    """
    Commands for managing local Kubernetes/Helm deployments.
    """
    pass


@k8s_app.command()
def deploy(
    release_name: str = typer.Argument("simmate", help="The helm release name."),
    template: bool = typer.Option(
        False,
        help="Render the Helm templates locally for debugging instead of deploying.",
    ),
):
    """
    Installs or upgrades the Simmate helm chart.
    """
    from simmate.config import settings

    k8s_values = settings.config_directory / "k8s-values.yaml"

    if template:
        logging.info(f"Running helm template for release {release_name}...")
        subprocess.run(
            f"helm template {release_name} envs/helm --debug -f {k8s_values}",
            shell=True,
        )
    else:
        logging.info(f"Running helm upgrade --install for release {release_name}...")
        subprocess.run(
            f"helm upgrade --install {release_name} envs/helm -f {k8s_values}",
            shell=True,
        )


@k8s_app.command()
def exec():
    """
    Lists all Simmate pods and prompts the user to select one to enter.
    """
    logging.info("Finding simmate pods...")
    try:
        output = (
            subprocess.check_output(
                "kubectl get pods -o jsonpath='{.items[*].metadata.name}'",
                shell=True,
            )
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        logging.error("Could not run kubectl command.")
        raise typer.Exit(1)

    pods = [p for p in output.split() if "simmate" in p]
    pods.sort()

    if not pods:
        logging.error("Could not find any simmate pods.")
        raise typer.Exit(1)

    for i, pod in enumerate(pods):
        typer.echo(f"[{i}] {pod}")

    choice = typer.prompt("Enter the index of the pod to enter", type=int)

    if choice < 0 or choice >= len(pods):
        logging.error("Invalid choice.")
        raise typer.Exit(1)

    pod = pods[choice]
    logging.info(f"Opening bash in pod: {pod}")
    subprocess.run(f"kubectl exec -it {pod} -- /bin/bash", shell=True)


@k8s_app.command()
def scale(
    replicas: int = typer.Argument(..., help="The number of replicas to scale to."),
    service: str = typer.Option("worker", help="The service to scale."),
):
    """
    Scales a Simmate deployment to the specified number of replicas.
    """
    logging.info(f"Scaling {service} to {replicas} replicas...")
    subprocess.run(
        f"kubectl scale deployment simmate-{service}-deployment --replicas={replicas}",
        shell=True,
    )


def _get_gunicorn_pod() -> str:
    try:
        pod = (
            subprocess.check_output(
                "kubectl get pods -l app=simmate-gunicorn -o jsonpath='{.items[0].metadata.name}'",
                shell=True,
            )
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        logging.error("Could not run kubectl command.")
        raise typer.Exit(1)

    if not pod:
        logging.error("Could not find a gunicorn pod.")
        raise typer.Exit(1)

    return pod


@k8s_app.command()
def update_static():
    """
    Copies static files from the gunicorn pod to the shared /staticfiles volume.
    """
    logging.info("Finding gunicorn pod...")
    pod = _get_gunicorn_pod()

    logging.info("Copying static files to /staticfiles volume...")
    subprocess.run(
        f"kubectl exec -it {pod} -- sh -c 'cp -r /root/simmate/src/simmate/website/static/* /staticfiles/'",
        shell=True,
    )


@k8s_app.command()
def update_db():
    """
    Runs `simmate database update` inside the gunicorn pod.
    """
    logging.info("Finding gunicorn pod...")
    pod = _get_gunicorn_pod()

    logging.info("Running `simmate database update`...")
    subprocess.run(f"kubectl exec -it {pod} -- simmate database update", shell=True)
