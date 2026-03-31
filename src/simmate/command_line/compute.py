# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate computational resources. All commands are
accessible through the "simmate compute" command.
"""

import typer

compute_app = typer.Typer(rich_markup_mode="markdown")


@compute_app.callback(no_args_is_help=True)
def compute():
    """
    Commands for managing computational resources, including workers, clusters,
    and task scheduling.
    """
    pass


@compute_app.command()
def start_schedules():
    """
    Starts the main scheduler process for periodic tasks.

    This command monitors the "schedules" module of each registered app and
    triggers tasks at their defined intervals.
    """
    from simmate.workflows.scheduler import SimmateScheduler

    SimmateScheduler.start()


@compute_app.command()
def start_worker(
    nitems_max: int = typer.Option(
        None,
        help="The maximum number of workflow runs to complete before shutting down.",
    ),
    timeout: float = typer.Option(
        None,
        help="The maximum time (in seconds) the worker should run before shutting down.",
    ),
    close_on_empty_queue: bool = typer.Option(
        False,
        help="Whether the worker should shut down if the job queue is empty.",
    ),
    waittime_on_empty_queue: float = typer.Option(
        1,
        help="The time (in seconds) to wait before re-checking the queue when it is empty.",
    ),
    tag: list[str] = typer.Option(
        ["simmate"],
        help="Tags to filter jobs by. Only jobs with these tags will be executed. Multiple tags can be provided.",
    ),
    startup_method: str = typer.Option(
        None,
        help="The method used to start the worker (e.g. for multiprocessing).",
    ),
):
    """
    Starts a Simmate Worker to execute jobs from the queue.

    Workers continuously query the database for new jobs that match their tags
    and execute them.
    """

    from simmate.workflows import Worker

    worker = Worker(
        nitems_max=nitems_max,
        timeout=timeout,
        close_on_empty_queue=close_on_empty_queue,
        waittime_on_empty_queue=waittime_on_empty_queue,
        tags=tag,  # this is actually "tags" --> a list of strings
        startup_method=startup_method,
    )
    worker.start()


@compute_app.command()
def start_singleflow_worker():
    """
    Starts a Simmate Worker that executes exactly one job and then shuts down.

    This is a convenience command equivalent to:
    `simmate compute start-worker --nitems-max 1 --close-on-empty-queue`
    """

    from simmate.workflows import Worker

    Worker.run_singleflow_worker()


@compute_app.command()
def start_cluster(
    nworkers: int = typer.Argument(
        ...,
        help="The number of workers to maintain in the cluster.",
    ),
    type: str = typer.Option(
        "local",
        help="The type of cluster to start. Options include 'local' and 'slurm'.",
    ),
    continuous: bool = typer.Option(
        False,
        help="If true, the cluster will continuously submit new workers to maintain `nworkers` until stopped.",
    ),
):
    """
    Starts and manages a cluster of Simmate Workers.
    """

    from simmate.compute.utils import start_cluster

    start_cluster(
        nworkers=nworkers,
        cluster_type=type,
        continuous=continuous,
    )


@compute_app.command()
def error_summary():
    """
    Displays a summary of error messages for all failed jobs in the database.
    """
    from simmate.compute import SimmateExecutor

    SimmateExecutor.show_error_summary()


@compute_app.command()
def stats():
    """
    Displays high-level statistics for all jobs (Pending, Running, Finished, etc.).
    """
    from simmate.compute import SimmateExecutor

    SimmateExecutor.show_stats()


@compute_app.command()
def stats_detail(
    tag: list[str] = typer.Option(
        [],
        help="Filter statistics by job tags.",
    ),
    recent: float = typer.Option(
        None,
        help="Filter statistics to jobs updated within the last N hours.",
    ),
):
    """
    Displays detailed job statistics with optional filtering by tags and time.
    """
    from simmate.compute import SimmateExecutor

    SimmateExecutor.show_stats_detail(
        tags=tag,
        recent=recent,
    )


@compute_app.command()
def workitems(
    tag: list[str] = typer.Option(
        [],
        help="Filter the job list by tags.",
    ),
    status: str = typer.Option(
        None,
        help="Filter by job status (P=Pending, R=Running, F=Finished, E=Error, C=Cancelled).",
    ),
    recent: float = typer.Option(
        None,
        help="Filter to jobs updated within the last N hours.",
    ),
):
    """
    Displays a tabular list of jobs and their current status.
    """
    from simmate.compute import SimmateExecutor

    SimmateExecutor.show_workitems(
        tags=tag,
        status=status,
        recent=recent,
    )


@compute_app.command()
def delete_finished(
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Automatically confirm deletion.",
    )
):
    """
    Deletes all jobs with a 'Finished' status from the database.
    """
    from simmate.compute import SimmateExecutor

    SimmateExecutor.delete_finished(confirm)


@compute_app.command()
def delete_all(
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Automatically confirm deletion.",
    )
):
    """
    Deletes ALL jobs from the database, regardless of status.
    """
    from simmate.compute import SimmateExecutor

    SimmateExecutor.delete_all(confirm)


@compute_app.command()
def delete(
    tag: list[str] = typer.Option(
        [],
        help="The tags of the jobs to be deleted.",
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Automatically confirm deletion.",
    ),
):
    """
    Deletes jobs from the database that match the provided tags.
    """
    from simmate.compute import SimmateExecutor

    SimmateExecutor.delete(tags=tag, confirm=confirm)
