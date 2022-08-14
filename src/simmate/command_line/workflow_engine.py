# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate workflow engine. All commands are 
accessible through the "simmate workflow-engine" command.
"""

import click


@click.group()
def workflow_engine():
    """
    A group of commands for starting up Simmate Workers, Prefect Agents, and
    Dask Clusters. These are meant for setting up remote computational resources.
    """
    pass


@workflow_engine.command()
@click.option(
    "--nitems_max",
    "-n",
    default=None,
    type=int,
    help="the number of task run to submit before shutdown",
)
@click.option(
    "--timeout",
    "-t",
    default=None,
    type=float,
    help="the time (in seconds) after which this worker will stop running jobs and shutdown",
)
@click.option(
    "--close_on_empty_queue",
    "-e",
    default=False,
    type=bool,
    help="whether to shutdown when the queue is empty",
)
@click.option(
    "--waittime_on_empty_queue",
    "-w",
    default=1,
    type=float,
    help=(
        "if the queue is empty, the time (in seconds) the worker should wait"
        " before checking the queue again"
    ),
)
@click.option(
    "--tags",
    "-t",
    default=["simmate"],
    help="tags to filter tasks by for submission. defaults to just 'simmate'",
    multiple=True,
)
def start_worker(
    nitems_max,
    timeout,
    close_on_empty_queue,
    waittime_on_empty_queue,
    tags,
):
    """
    This starts a Simmate Worker which will query the database for jobs to run.
    """

    from simmate.workflow_engine import Worker

    worker = Worker(
        nitems_max,
        timeout,
        close_on_empty_queue,
        waittime_on_empty_queue,
        tags,
    )
    worker.start()


@workflow_engine.command()
def start_singleflow_worker():
    """
    This starts a Simmate Worker that only runs one job and then shuts down. Also,
    if no job is available in the queue, it will shut down.

    Note: this can be acheived using the start-worker command too, but because
    this is such a common use-case, we include this command for convienence.
    It is the same as...

    simmate workflow-engine start-worker -n 1 -e True -t simmate
    """

    from simmate.workflow_engine import Worker

    Worker.run_singleflow_worker()


@workflow_engine.command()
@click.argument(
    "nworkers",
    type=int,
)
@click.option(
    "--worker_command",
    "-c",
    default="simmate workflow-engine start-worker",
    type=str,
    help="the command to start each worker with. See start-worker for options",
)
def start_cluster(nworkers, worker_command):
    """
    This starts many Simmate Workers that each run in a local subprocess.
    """

    from simmate.workflow_engine.execution.utilities import start_cluster

    start_cluster(
        nworkers=nworkers,
        worker_command=worker_command,
    )


# explicitly list functions so that pdoc doesn't skip them
__all__ = [
    "workflow_engine",
    "start_worker",
    "start_singleflow_worker",
    "start_cluster",
]
