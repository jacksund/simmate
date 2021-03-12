# -*- coding: utf-8 -*-


def setup_warwulf():
    """

    ------PREFECT_AGENT.PY------
    from simmate.configuration.prefect.agents_and_clusters import setup_warwulf
    setup_warwulf()

    ------IN TERMINAL------
    nohup redshift &
    based on advice from...
    https://unix.stackexchange.com/questions/4004/how-can-i-run-a-command-which-will-survive-terminal-close

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

    from simmate.configuration.dask.warwulf import setup_cluster

    cluster = setup_cluster()

    from prefect.agent.local import LocalAgent

    agent = LocalAgent(
        name="WarWulf",
        # max_polls=1,
        labels=["DESKTOP-PVN50G5"]
        # no_cloud_logs=True
    )
    agent.start()
