# -*- coding: utf-8 -*-

import os


def setup_warwulf():
    """

    ------PREFECT_AGENT.PY------
    from simmate.configuration.prefect.agents_and_clusters import setup_warwulf
    setup_warwulf()

    ------IN TERMINAL------
    nohup python prefect_agent.py &
    based on advice from...
    https://unix.stackexchange.com/questions/4004/how-can-i-run-a-command-which-will-survive-terminal-close
    to cancel...
    ps -aef | grep python # to find id
    kill <id>

    ------SUBMIT.SH------
    #!/bin/bash

    #SBATCH --job-name=prefect_agent
    #SBATCH --output=slurm.out
    #SBATCH --nodes=1
    #SBATCH --ntasks=1
    #SBATCH --cpus-per-task 1
    #SBATCH --partition=p1
    #SBATCH --time=400-00:00

    # Load modules
    module load intel
    module load impi
    module load vasp

    # set python env
    #conda activate jacks_env

    # run Prefect
    python prefect_agent.py
    """

    # Setup up the Dask cluster using the pre-defined settings
    from simmate.configuration.dask.warwulf import setup_cluster

    cluster = setup_cluster()

    # All workflows should be pointed to the Dask cluster as the default Executor.
    # We can grab the Dask scheduler's address using the cluster object from above.
    # For the master node, this address is "tcp://152.2.172.72:8786"
    os.environ.setdefault(
        "PREFECT__ENGINE__EXECUTOR__DEFAULT_CLASS", "prefect.executors.DaskExecutor"
    )
    os.environ.setdefault(
        "PREFECT__ENGINE__EXECUTOR__DASK__ADDRESS", cluster.scheduler.address
    )

    from prefect.agent.local import LocalAgent

    agent = LocalAgent(
        name="WarWulf",
        # max_polls=1,
        labels=["DESKTOP-PVN50G5"]
        # no_cloud_logs=True
    )
    agent.start()
