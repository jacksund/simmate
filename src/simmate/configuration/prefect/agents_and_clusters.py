# -*- coding: utf-8 -*-

def setup_warwulf():
    """
    from simmate.configuration.prefect import setup_warwulf_cluster_and_agent
    setup_warwulf_cluster_and_agent()

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
