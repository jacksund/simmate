# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

# STEP 1: Configure our Dask Cluster.

from dask_jobqueue import SLURMCluster

cluster = SLURMCluster(
    #
    # General options
    scheduler_options={"port": 8786},
    local_directory="~",
    #
    #
    # Dask Worker Options
    cores=1,
    processes=1,
    memory="4GB",
    # REQUIRED: Make sure you preload this script!
    extra=["--preload simmate.configuration.dask.connect_to_database"],
    #
    #
    # SLURM Job Options
    job_cpu=18,
    job_mem="50GB",
    job_extra=[
        "--output=slurm-%j.out",
        "-N 1",
    ],
    walltime="300-00:00:00",
    queue="p1",
    env_extra=["module load vasp;"],
)

# Scale the cluster to the number of SLURM jobs that you'd like
cluster.scale(10)

# --------------------------------------------------------------------------------------

# STEP 2: Configure our Prefect Agent and start submitting workflows!

from prefect.agent.local import LocalAgent
from simmate.configuration.prefect.connect_to_dask import set_default_executor

# We want Prefect to use our Dask Cluster to run all of the workflow tasks. To
# tell Prefect to do this, we wrote a helper function that ships with Simmate.
set_default_executor(cluster.scheduler.address)

agent = LocalAgent(
    name="WarWulf",
    labels=["DESKTOP-PVN50G5", "digital-storm"],
)

# Now we can start the Prefect Agent which will run and search for jobs and then
# submit them to our Dask cluster.
agent.start()
# NOTE: this line will run endlessly unless you set a timelimit in the LocalAgent above

# --------------------------------------------------------------------------------------
