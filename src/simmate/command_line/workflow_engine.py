# -*- coding: utf-8 -*-

import click


@click.group()
def workflow_engine():
    """
    A group of commands for starting up Prefect Agents and Dask Clusters. 
    There is also a simple "Simmate Cluster" that you can use too, but it 
    is only meant for quick testing.
    
    Setting up your computational resources can be tricky, so be sure to go 
    through our tutorial before trying this on your own: <TODO: INSERT LINK>
    """
    pass


@workflow_engine.command()
@click.option(
    "--prefect_config", "-p", help="the name of the Prefect Agent configuration to use",
)
@click.option(
    "--dask_config", "-d", help="the name of the Dask Cluster configuration to use",
)
def start_warwulf_cluster(prefect_config, dask_config):
    """
    This starts up a Dask cluster and/or a Prefect Agent that can run Simmate jobs.

    This convenience command is really only meant for testing purposes, as Dask
    and Prefect teams offer their own commands with much more control. For
    example, this command uses Prefect's LocalAgent, but there are other
    advanced types available such as DockerAgent which may be better for your
    use case.

    If you would like this cluster to run endlessly in the background, you can
    submit it with something like "nohup simmate cluster start <<extra-options>> &".
    The "nohup" and "&" symbol together make it so this runs in the background AND
    it won't shutdown if you close your terminal (or ssh).

    For more help on managing your computational resources, see here:
        <<TODO: insert link>>

    """

    click.echo("Setting up Dask Cluster and Prefect Agent...")

    # For now I just use my hard-coded script here, but this will change in the
    # future.
    from simmate.configuration.prefect.agents_and_clusters import setup_warwulf

    setup_warwulf()


@workflow_engine.command()
@click.option(
    "--nitems_max",
    "-n",
    default=None,
    help="the number of jobs to run before shutdown",
)
@click.option(
    "--timeout",
    "-t",
    default=None,
    help="the time (in seconds) after which this worker will stop running jobs and shutdown",
)
@click.option(
    "--close_on_empty_queue",
    "-c",
    default=False,
    help="whether to shutdown or not when the queue is empty",
)
@click.option(
    "--waittime_on_empty_queue",
    "-w",
    default=60,
    help="how long to wait before checking again when the queue is found to be empty",
)
def start_worker(nitems_max, timeout, close_on_empty_queue, waittime_on_empty_queue):
    """
    This starts a Simmate Worker which will query the database for jobs to run.

    """

    from simmate.workflow_engine.execution.worker import SimmateWorker

    worker = SimmateWorker(
        nitems_max=nitems_max,
        timeout=timeout,
        close_on_empty_queue=close_on_empty_queue,
        waittime_on_empty_queue=waittime_on_empty_queue,
    )
    worker.start()


@workflow_engine.command()
def start_singletask_worker():
    """
    This starts a Simmate Worker that only runs one job and then shuts down. Also,
    if no job is available in the queue, it will shut down.
    
    Note: this can be acheived using the start-worker command too, but because
    this is such a common use-case, we include this command for convienence.
    It is the same as...
    
    simmate start-worker -n 1 -c True

    """

    from simmate.workflow_engine.execution.worker import SimmateWorker

    worker = SimmateWorker(
        nitems_max=1,
        timeout=None,
        close_on_empty_queue=True,
        waittime_on_empty_queue=0.1,
    )
    worker.start()
