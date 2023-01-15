# -*- coding: utf-8 -*-

from simmate.engine.execution.cluster import LocalCluster, SlurmCluster


def start_cluster(
    nworkers: int,
    cluster_type: str = "local",
    continuous: bool = False,
):
    """
    Utilitiy that helps set up common cluster types with a specific number of
    workers and optionally run a single-submit of workers
    """
    if cluster_type == "local":
        cluster = LocalCluster
    elif cluster_type == "slurm":
        cluster = SlurmCluster
    else:
        raise Exception(f"Unknown cluster type {cluster_type}. Choose local or slurm.")

    if continuous:
        cluster.start_cluster(nworkers)
    else:
        jobs = cluster.submit_jobs(nworkers)
        if cluster_type == "local":
            cluster.wait_for_jobs(jobs)
