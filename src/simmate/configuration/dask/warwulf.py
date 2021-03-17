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

# BUG: for scaling Dask to many workers, I initially ran into issues of "too many
# files open". This is addressed in Dask's FAQ:
#   https://distributed.dask.org/en/latest/faq.html#too-many-open-file-descriptors
# To summarize the fix...
#   (1) check the current soft limit (soft = no sudo permissions) for  files
#       ulimit -Sn
#   (2) to increase the softlimit, edit the limits.conf file and add one line
#       sudo nano /etc/security/limits.conf
#           # add this line below
#           * soft nofile 10240
#   (3) close and reopen the terminal
#   (4) confirm we changed the limit
#       ulimit -Sn
#
# This may also be a leak of sockets being left open by Dask:
#   (1) get the PID of the running process with
#       ps -aef | grep python
#   (2) look at the fd's (file opened) by the given process
#       cd /proc/<PID>/fd; ls -l
#   (3) count the number of files opened by the given process
#       ls /proc/<PID>/fd/ | wc -l
#   (4) view overall stats with
#       cat /proc/<PID>/net/sockstat
#   (5) another option to list open files is
#       lsof -p <PID> | wc -l
#
# Whenever I see a heartbeat fail, I also see a massive jump in the number of
# files opened by the process. I believe zombie prefect runs are creating
# a socket leak.
#

# nworkers_min=5, nworkers_max=25 BUG: adaptive deploy removed for now
def setup_cluster(nworkers=25):

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
        memory="50GB",
        extra=["--preload simmate.configuration.dask.init_django_worker"],
        # BUG: dask-jobqueue doesn't support our preferred kwargs format...
        #   {"preload": "simmate.configuration.dask.init_django_worker"}
        #
        #
        # Slurm Settings
        job_cpu=16,  # --cpus-per-task, -c
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

    # Start scaling the number of Dask workers based on how busy the Scheduler is.
    # TODO: should I just return the cluster and leave the user to adapt it?
    # cluster.adapt(minimum=nworkers_min, maximum=nworkers_max)
    # BUG: adaptive deploy is showing issues with fd leaking. I'm using scale for now.
    cluster.scale(nworkers)

    # print out info
    print(HEADER_ART)
    print(f"Scheduler is located at {cluster.scheduler.address}")
    print(f"Dashboard is located at {cluster.dashboard_link}")
    # !!! Removed adpative deploy for the time being
    # print(f"The number of Workers will scale between {workers_min} and {workers_max}")
    print(f"The number of Workers will be fixed at {nworkers}")
    # If you want to preview what the SLURM script looks like
    print("Workers are submitted to SLURM with the following submit.sh...\n")
    print(cluster.job_script())

    # connect to the cluster if you'd like to start submitting jobs
    # from dask.distributed import Client
    # client = Client(cluster)
    # client.submit(fxn, *args, **kwargs)

    return cluster
