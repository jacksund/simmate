# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate computational resources. All commands are
accessible through the "simmate compute" command.
"""

import typer

from simmate.command_line.utilities import AlphabeticalGroup

compute_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)


@compute_app.callback(no_args_is_help=True)
def compute():
    """
    Commands for managing computational resources, including workers, clusters,
    and task scheduling.
    """
    pass


worker_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)
cluster_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)
scheduler_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)
workitems_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)

compute_app.add_typer(worker_app, name="worker")
compute_app.add_typer(cluster_app, name="cluster")
compute_app.add_typer(scheduler_app, name="scheduler")
compute_app.add_typer(workitems_app, name="workitems")


@worker_app.callback(no_args_is_help=True)
def worker():
    """
    Commands for starting individual Simmate Workers.
    """
    pass


@cluster_app.callback(no_args_is_help=True)
def cluster():
    """
    Commands for starting and managing clusters of Simmate Workers.
    """
    pass


@scheduler_app.callback(no_args_is_help=True)
def scheduler():
    """
    Commands for running the scheduler of periodic tasks.
    """
    pass


@workitems_app.callback(no_args_is_help=True)
def workitems():
    """
    Commands for viewing and managing jobs (WorkItems) in the queue.
    """
    pass


@scheduler_app.command("start")
def start_scheduler():
    """
    Starts the main scheduler process for periodic tasks.

    This command monitors the "schedules" module of each registered app and
    triggers tasks at their defined intervals.
    """
    from simmate.database import connect  # isort:skip
    from simmate.compute import SimmateScheduler

    SimmateScheduler.start()


@worker_app.command("start")
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
    is_api_worker: bool = typer.Option(
        False,
        "--api",
        help="If provided, an API worker will be started using the URL specified in your simmate settings.",
    ),
):
    """
    Starts a Simmate Worker to execute jobs from the queue.

    Workers continuously query the database for new jobs that match their tags
    and execute them.
    """

    from simmate.database import connect  # isort:skip

    if is_api_worker:
        from simmate.compute import ApiWorker

        worker = ApiWorker(
            nitems_max=nitems_max,
            timeout=timeout,
            close_on_empty_queue=close_on_empty_queue,
            waittime_on_empty_queue=waittime_on_empty_queue,
            tags=tag,
            startup_method=startup_method,
        )
    else:
        from simmate.compute import SimmateWorker

        worker = SimmateWorker(
            nitems_max=nitems_max,
            timeout=timeout,
            close_on_empty_queue=close_on_empty_queue,
            waittime_on_empty_queue=waittime_on_empty_queue,
            tags=tag,  # this is actually "tags" --> a list of strings
            startup_method=startup_method,
        )

    worker.start()


@cluster_app.command("start")
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

    from simmate.database import connect  # isort:skip
    from simmate.compute.utils import start_cluster

    start_cluster(
        nworkers=nworkers,
        cluster_type=type,
        continuous=continuous,
    )


@workitems_app.command("list")
def list_workitems(
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

    from simmate.database import connect  # isort:skip
    from simmate.compute import SimmateExecutor

    SimmateExecutor.show_workitems(
        tags=tag,
        status=status,
        recent=recent,
    )


@workitems_app.command()
def stats(
    detail: bool = typer.Option(
        False,
        "--detail",
        help="Show detailed statistics. Implied when `--tag` or `--recent` is given.",
    ),
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
    Displays statistics for all jobs (Pending, Running, Finished, etc.).
    """

    from simmate.database import connect  # isort:skip
    from simmate.compute import SimmateExecutor

    if detail or tag or recent is not None:
        SimmateExecutor.show_stats_detail(
            tags=tag,
            recent=recent,
        )
    else:
        SimmateExecutor.show_stats()


@workitems_app.command()
def errors():
    """
    Displays a summary of error messages for all failed jobs in the database.
    """

    from simmate.database import connect  # isort:skip
    from simmate.compute import SimmateExecutor

    SimmateExecutor.show_error_summary()


@workitems_app.command()
def delete(
    tag: list[str] = typer.Option(
        [],
        help="Delete jobs that match these tags.",
    ),
    finished: bool = typer.Option(
        False,
        "--finished",
        help="Delete all jobs with a 'Finished' status.",
    ),
    all: bool = typer.Option(
        False,
        "--all",
        help="Delete ALL jobs, regardless of status.",
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm",
        help="Automatically confirm deletion.",
    ),
):
    """
    Deletes jobs from the database.

    By default, this deletes jobs that match the provided tags (or jobs with
    no tags if none are given). Use `--finished` or `--all` for bulk deletion.
    """

    if sum([bool(tag), finished, all]) > 1:
        raise typer.BadParameter(
            "Only one of `--tag`, `--finished`, or `--all` can be given."
        )

    from simmate.database import connect  # isort:skip
    from simmate.compute import SimmateExecutor

    if finished:
        SimmateExecutor.delete_finished(confirm)
    elif all:
        SimmateExecutor.delete_all(confirm)
    else:
        SimmateExecutor.delete(tags=tag, confirm=confirm)
