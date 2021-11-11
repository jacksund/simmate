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
def setup_cloud():
    """
    This configures Prefect Cloud for all of the Simmate Workflows. This includes
    registering them as well as organizing them into projects.

    If at any point you'd like to delete all of these and reset them, use the
    delete-cloud command followed by running this again.
    """
    click.echo("Building Prefect Projects and registering Simmate Workflows.")
    from simmate.configuration.prefect.projects import build

    build()


@workflow_engine.command()
def delete_cloud():
    """
    This clears your Prefect Cloud for all of the Simmate Projects and Workflows.

    To rebuild them, use the setup-cloud command. Note, you may have to wait
    a few minutes before running this second command because it takes a little
    for your deletion to take place in Prefect Cloud.
    """
    click.echo("Deleting all Prefect Projects and Simmate Workflows.")
    from simmate.configuration.prefect.projects import delete

    delete()


@workflow_engine.command()
@click.option(
    "--prefect_config",
    "-p",
    help="the name of the Prefect Agent configuration to use",
)
@click.option(
    "--dask_config",
    "-d",
    help="the name of the Dask Cluster configuration to use",
)
def start_cluster(prefect_config, dask_config):
    """
    This starts up a Dask cluster and/or a Prefect Agent that can run Simmate jobs.

    This convenience command is really only meant for testing purposes, as Dask
    and Prefect teams offer their own commands with much more control. For
    example, this command uses Prefect's LocalAgent, but there are other
    advanced types available such as DockerAgent which may be better for your
    use case.

    If you would like this cluster to run endlessly in the background, you can
    submit it with something like "nohup simmate workflow-engine start-cluster &".
    The "nohup" and "&" symbol together make it so this runs in the background AND
    it won't shutdown if you close your terminal (or ssh). To stop this from running,
    you'll now need to find the running process and kill it. Use something like
    "ps -aef | grep simmate" to find the running process and grab its ID. Then
    kill that process id with "kill 123" (if the id was 123).

    For more help on managing your computational resources, see here:
        <<TODO: insert link>>

    """

    click.echo("This command has not been implemented yet.")


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


@workflow_engine.command()
@click.option(
    "--nworkers",
    "-w",
    default=8,
    help="the number of separate slurm jobs to submit",
)
@click.option(
    "--cpus_per_worker",
    "-c",
    default=18,
    help="the number of cpus that each slurm job will request",
)
@click.option(
    "--memory_per_worker",
    "-m",
    default="50GB",
    help="the amount of memory that each slurm job will request",
)
@click.option(
    "--walltime_per_worker",
    "-t",
    default="300-00:00:00",
    help="the timelimit set for each slurm job",
)
@click.option(
    "--create_worker_directories",
    "-d",
    default=True,
    help="whether to create separate directories for each worker",
)
def start_warwulf_cluster(
    nworkers,
    cpus_per_worker,
    memory_per_worker,
    walltime_per_worker,
    create_worker_directories,
):
    """
    This sets up a Dask Cluster by submitting jobs to SLURM and then sets up a
    Prefect Agent that checks for scheduled workflows to run.

    This is just for the Warren Lab to use and will be removed in the future.
    """

    from simmate.configuration.dask.warwulf import setup_cluster
    from simmate.configuration.prefect.connect_to_dask import setup_env
    from prefect.agent.local import LocalAgent

    # Setup up the Dask cluster using the pre-defined settings
    cluster_address = setup_cluster(
        nworkers,
        cpus_per_worker,
        memory_per_worker,
        walltime_per_worker,
        create_worker_directories,
    )

    # We now want all Prefect workflows to use this cluster by default
    setup_env(cluster_address)

    # Now we can start the Prefect Agent which will run and search for jobs.
    agent = LocalAgent(
        name="WarWulf",
        labels=["DESKTOP-PVN50G5", "digital-storm"],
    )
    agent.start()
