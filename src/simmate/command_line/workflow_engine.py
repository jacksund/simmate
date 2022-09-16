# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate workflow engine. All commands are 
accessible through the "simmate workflow-engine" command.
"""

import typer

workflow_engine_app = typer.Typer(rich_markup_mode="markdown")


@workflow_engine_app.callback(no_args_is_help=True)
def workflow_engine():
    """
    A group of commands for starting up computational resources (Workers,
    Agents, and Clusters)
    """
    pass


@workflow_engine_app.command()
def start_worker(
    nitems_max: int = None,
    timeout: float = None,
    close_on_empty_queue: bool = False,
    waittime_on_empty_queue: float = 1,
    tag: list[str] = ["simmate"],
):
    """
    Starts a Simmate Worker which will query the database for jobs to run

    By default this worker will run endlessly and not close.

    - `nitems_max`: the number of task run to submit before shutdown
    - `timeout`: the time (in seconds) after which this worker will stop running
    jobs and shutdown

    - `close_on_empty_queue`: whether the worker should shut down when the
    queue is empty

    - `waittime_on_empty_queue`: if the queue is empty, the time (in seconds)
    the worker should wait before checking the queue again

    - `tags`: tags to filter tasks by for submission. defaults to just 'simmate'

    """

    from simmate.workflow_engine import Worker

    worker = Worker(
        nitems_max,
        timeout,
        close_on_empty_queue,
        waittime_on_empty_queue,
        tag,  # this is actually "tags" --> a list of strings
    )
    worker.start()


@workflow_engine_app.command()
def start_singleflow_worker():
    """
    This starts a Simmate Worker that only runs one job and then shuts down. Also,
    if no job is available in the queue, it will shut down.

    Note: this can be acheived using the start-worker command too, but because
    this is such a common use-case, we include this command for convienence.
    It is the same as...

    `simmate workflow-engine start-worker --nitems-max 1 --close-on-empty-queue`
    """

    from simmate.workflow_engine import Worker

    Worker.run_singleflow_worker()


@workflow_engine_app.command()
def start_cluster(
    nworkers: int,
    type: str = "local",
    continuous: bool = False,
):
    """
    This starts many Simmate Workers that each run in a local subprocess

    - `nworkers`: the number of workers to start

    - `cluster_type`: where to submit workers (either local or slurm)

    - `continuous`: whether to do a single submission of workers or hold nworkers
    at a steady-state number (runs endlessly)

    """

    from simmate.workflow_engine.execution.utilities import start_cluster

    start_cluster(
        nworkers=nworkers,
        cluster_type=type,
        continuous=continuous,
    )


@workflow_engine_app.command()
def show_error_summary():
    """
    Prints the shorthand error for all failed jobs
    """
    from simmate.workflow_engine.execution import SimmateExecutor

    SimmateExecutor.show_error_summary()


@workflow_engine_app.command()
def show_stats():
    """
    Prints a summary of different workitems and their status
    """
    from simmate.workflow_engine.execution import SimmateExecutor

    SimmateExecutor.show_stats()


@workflow_engine_app.command()
def delete_finished(confirm: bool = False):
    """
    Deletes all finished workitems from the database
    """
    from simmate.workflow_engine.execution import SimmateExecutor

    SimmateExecutor.delete_finished(confirm)


@workflow_engine_app.command()
def delete_all(confirm: bool = False):
    """
    Deletes all workitems from the database
    """
    from simmate.workflow_engine.execution import SimmateExecutor

    SimmateExecutor.delete_all(confirm)
