# -*- coding: utf-8 -*-

# To learn more on Dask configuration, I should read...
#   https://docs.dask.org/en/latest/configuration.html#dask.config.set


from dask_jobqueue import SLURMCluster

HEADER_ART = r"""
 ____            _       ____ _           _
|  _ \  __ _ ___| | __  / ___| |_   _ ___| |_ ___ _ __
| | | |/ _` / __| |/ / | |   | | | | / __| __/ _ \ '__|
| |_| | (_| \__ \   <  | |___| | |_| \__ \ ||  __/ |
|____/ \__,_|___/_|\_\  \____|_|\__,_|___/\__\___|_|

"""

# nworkers_min=5, nworkers_max=25 BUG: adaptive deploy removed for now
def setup_cluster(
    nworkers=8,
    cpus_per_worker=18,
    memory_per_worker="50GB",
    walltime_per_worker="300-00:00:00",
    create_worker_directories=True,
    extra_worker_commands=None,  # give as a list. ex: ["module load vasp", ...]
):

    # First let's see what commands each worker should run before starting any
    # jobs. If none were provided, we start with an empty list
    extra_worker_commands = extra_worker_commands if extra_worker_commands else []
    # If the we want a separate working directory for each worker, then we add
    # one extra command that creates it and moves in to the new directory.
    # The folder will be named after the SLURM job id to ensure they are all
    # unique and can be tracked.
    extra_worker_commands.append(
        "mkdir daskworker-$SLURM_JOBID; cd daskworker-$SLURM_JOBID;"
    )

    # Consider moving the configuration settings to ~/.config/dask/jobqueue.yaml
    # NOTE: I request SLURM settings much higher than Dask worker settings. This
    # is because I want to launch commands via mpirun.

    cluster = SLURMCluster(
        # Dask Scheduler Settings
        scheduler_options={"port": 8786},  # BUG: this should be the default already
        #
        #
        # Dask Worker Settings
        local_directory="~",  # moves dask-worker-space off the shared drive for speed
        cores=1,
        processes=1,
        memory=memory_per_worker,
        # This script ensures we have django configured for each worker
        extra=["--preload simmate.configuration.dask.connect_to_database"],
        #
        #
        # Slurm Settings
        job_cpu=cpus_per_worker,  # --cpus-per-task, -c
        job_mem=memory_per_worker,  # --mem
        job_extra=[
            "--output=slurm-%j.out",
            "-N 1",  # --nodes
            # This overwrites Dask's default. Confirm this with "echo $SLURM_NTASKS"
            # '-n 1' # --ntasks
        ],
        walltime=walltime_per_worker,  # --time, -t
        queue="p1",  # --partition, -p
        #
        #
        # Commands to run before staring dask-worker
        env_extra=extra_worker_commands,
        #
        #
        # Extras
        # if conda activate isnt working, I can set the python to use manually
        # python="/opt/ohpc/pub/apps/anaconda/anaconda3/envs/jacks_env/bin/python",
        # Some clusters benefit from using an interface
        # You can see which are available with the ifconfig command on linux
        # interface="eth0",
        # scheduler_options={'interface':'eno1'},
    )

    # Start scaling the number of Dask workers based on how busy the Scheduler is.
    # TODO: should I just return the cluster and leave the user to adapt it?
    # cluster.adapt(minimum=nworkers_min, maximum=nworkers_max)
    # BUG: adaptive deploy is showing issues with fd leaking. I'm using scale for now.
    cluster.scale(nworkers)

    # print out info
    print(HEADER_ART)
    print(f"Scheduler is located at {cluster.scheduler.address}")
    print(f"Dashboard is located at {cluster.dashboard_link}")
    print(
        "To view the dashboard via ssh, use the command... \n\t"
        "ssh -N -L 8787:warwulf.net:8787 WarrenLab@warwulf.net"
    )
    # !!! Removed adpative deploy for the time being
    # print(f"The number of Workers will scale between {workers_min} and {workers_max}")
    print(f"The number of Workers will be fixed at {nworkers}")
    # If you want to preview what the SLURM script looks like
    print("Workers are submitted to SLURM with the following submit.sh...\n")
    print(cluster.job_script())

    return cluster.scheduler.address
