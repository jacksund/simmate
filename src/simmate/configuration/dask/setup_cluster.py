# -*- coding: utf-8 -*-

from dask.distributed import LocalCluster
import dask_jobqueue
from distributed.deploy.spec import SpecCluster


# These are the different Cluster types that you can import from dask_jobqueue
# TODO: Is there a way to dynamically determine this?
ALLOWED_CLUSTER_TYPES = [
    "Local",
    "PBS",
    "SLURM",
    "SGE",
    "HTCondor",
    "LSF",
    "Moab",
    "OAR",
]

HEADER_ART = r"""
 ____            _       ____ _           _
|  _ \  __ _ ___| | __  / ___| |_   _ ___| |_ ___ _ __
| | | |/ _` / __| |/ / | |   | | | | / __| __/ _ \ '__|
| |_| | (_| \__ \   <  | |___| | |_| \__ \ ||  __/ |
|____/ \__,_|___/_|\_\  \____|_|\__,_|___/\__\___|_|

"""


def run_cluster(
    cluster_type: str = "Local",
    n_workers: int = None,
    **cluster_kwargs,
) -> SpecCluster:

    # make sure we have a legal cluster type
    if cluster_type not in ALLOWED_CLUSTER_TYPES:
        raise Exception(
            f"{cluster_type} is not an allowed cluster type."
            f"Please choose one of the following: {ALLOWED_CLUSTER_TYPES}"
        )

    # Start a local cluster with default settings if requested
    if cluster_type == "Local":
        cluster = LocalCluster(
            n_workers=n_workers,
            preload="simmate.configuration.dask.connect_to_database",
            **cluster_kwargs,
        )

    # otherwise we have a jobqueue cluster
    else:
        # grab the class from the module. It will be named something like PBSCluster
        ClusterClass = getattr(dask_jobqueue, f"{cluster_type}Cluster")
        # Now initialize the cluster using the default Dask config.
        cluster = ClusterClass(**cluster_kwargs)
        if not n_workers:
            raise Exception("You must provide n_workers when using a JobQueue cluster")
        cluster.scale(n_workers)

    # print some info about the cluster for the user
    print(HEADER_ART)
    print(f"Scheduler is located at {cluster.scheduler.address}")
    print(f"Dashboard is located at {cluster.dashboard_link}")
    print(
        "To view the dashboard via ssh, use a command like... \n\t"
        "ssh -N -L 8787:example.net:8787 exampleuser@example.net"
    )
    # Also if we have a jobqueue, we can display the submit script being used.
    if issubclass(cluster.__class__, dask_jobqueue.JobQueueCluster):
        print("Workers are submitted to a jobqueue with the following script...\n")
        print(cluster.job_script())
    else:
        print("Workers are all ran on the local machine.")
    print("\n\n")

    return cluster
