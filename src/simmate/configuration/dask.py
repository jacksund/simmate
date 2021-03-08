# -*- coding: utf-8 -*-

# To learn more on Dask configuration, I should read...
#   https://docs.dask.org/en/latest/configuration.html#dask.config.set


from dask_jobqueue import SLURMCluster

HEADER_ART = r"""
   ___           __     _______         __
  / _ \___ ____ / /__  / ___/ /_ _____ / /____ ____
 / // / _ `(_-</  '_/ / /__/ / // (_-</ __/ -_) __/
/____/\_,_/___/_/\_\  \___/_/\_,_/___/\__/\__/_/

"""


def setup_warwulf_cluster():

    # Consider moving the configuration settings to ~/.config/dask/jobqueue.yaml
    # NOTE: I request SLURM settings much higher than Dask worker settings. This
    # is because I want to launch commands via mpirun.

    cluster = SLURMCluster(
        #
        #
        # Dask Worker Settings
        local_directory="~",  # moves dask-worker-space off the shared drive for speed
        cores=1,
        processes=1,
        memory="4GB",
        #
        #
        # Slurm Settings
        job_cpu=20,  # --cpus-per-task, -c
        job_mem="50GB",  # --mem
        job_extra=[
            "--output=slurm-%j.out",
            "-N 1",  # --nodes
            # This overwrites Dask's default. Confirm this with "echo $SLURM_NTASKS"
            # '-n 1' # --ntasks
        ],
        walltime="300-00:00:00",  # --time, -t
        queue="p1",  # --partition, -p
        #
        #
        # Commands to run before staring dask-worker
        env_extra=[
            # This makes a folder named after the SLURM job id and moves into it.
            # I need this because of Custodian -- I give each worker its own directory.
            "mkdir daskworker-$SLURM_JOBID; cd daskworker-$SLURM_JOBID;",
            # Load modules
            # module load intel
            # module load impi
            # module load vasp
            # set python env
            # conda activate jacks_env
        ],
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

    # If you want to preview what the SLURM script looks like
    # print(cluster.job_script())

    # Start scaling the number of Dask workers based on how busy the Scheduler is
    cluster.adapt(minimum=1, maximum=15)

    # print out info
    print(HEADER_ART)
    print(f"Scheduler is located at {cluster.scheduler.address}")
    print(f"Dashboard is located at {cluster.dashboard_link}")
    print("\n\n\n")

    # connect to the cluster if you'd like to start submitting jobs
    # from dask.distributed import Client
    # client = Client(cluster)
    # client.submit(fxn, *args, **kwargs)

    return cluster
