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
    "--agent_name",
    "-n",
    help="the name of the agent that will be visible in prefect cloud",
)
@click.option(
    "--agent_labels",
    "-l",
    help="labels that the agent will query for. To list multiple do... -l label1 -l label2",
    multiple=True,
)
@click.option(
    "--njobs",
    "-j",
    help="the number of separate slurm jobs to submit",
    type=int,
)
@click.option(
    "--cpus_per_job",
    "-c",
    help="the number of cpus that each slurm job will request",
    type=int,
)
@click.option(
    "--memory_per_job",
    "-m",
    help="the amount of memory that each slurm job will request",
)
@click.option(
    "--walltime_per_job",
    "-t",
    help="the timelimit set for each slurm job",
)
def run_cluster(
    agent_name,
    agent_labels,
    njobs,
    cpus_per_job,
    memory_per_job,
    walltime_per_job,
):
    """
    This starts up a Dask cluster and a Prefect Agent in order to run Simmate jobs.

    This convenience command is really only meant for testing purposes, as Dask
    and Prefect teams offer their own commands with much more control. For
    example, this command uses Prefect's LocalAgent, but there are other
    advanced types available such as DockerAgent which may be better for your
    use case.

    If you would like this cluster to run endlessly in the background, you can
    submit it with something like "nohup simmate workflow-engine run-cluster &".
    The "nohup" and "&" symbol together make it so this runs in the background AND
    it won't shutdown if you close your terminal (or ssh). To stop this from running,
    you'll now need to find the running process and kill it. Use something like
    "ps -aef | grep simmate" to find the running process and grab its ID. Then
    kill that process id with "kill 123" (if the id was 123).

    For more help on managing your computational resources, see here:
        <<TODO: insert link>>

    """

    from simmate.configuration.prefect.setup_resources import run_cluster_and_agent

    # agent_name and agent_labels are optional. We want them to grab the config defaults
    # if they weren't passed, so check if they were set here.
    agent_kwargs = {}
    if agent_name:
        agent_kwargs["agent_name"] = agent_name
    if agent_labels:
        agent_kwargs["agent_labels"] = agent_labels

    run_cluster_and_agent(
        njobs=njobs,
        job_cpu=cpus_per_job,
        job_mem=memory_per_job,
        walltime=walltime_per_job,
        **agent_kwargs,
    )
