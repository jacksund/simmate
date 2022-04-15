# -*- coding: utf-8 -*-

from dask.distributed import Client, get_client


def get_dask_client(**kwargs) -> Client:
    """
    This is a convenience utility that grabs the client for the local Dask cluster
    if it exists -- and if not, creates a new cluster and returns the client for
    it.

    #### Parameters

    - `**kwargs`:
        Any arguments normally accepted by dask.distributed.Client. The exception
        to this is the `preload` kwarg, which is not allowed.
    """

    # First, try accessing a global client.
    try:
        client = get_client()
    # If the line above fails, it's because no global client exists yet. In that
    # case, we make a new cluster and return the client for it.
    except ValueError:
        # This preload script connects each worker to the Simmate database
        client = Client(
            preload="simmate.configuration.dask.connect_to_database",
            **kwargs,
        )
        # TODO: To all default job-queue clusters, consider using...
        # from simmate.configuration.dask.setup_cluster import run_cluster
        # cluster = run_cluster(...)
        # client = Client(cluster.scheduler.address)

    # OPTIMIZE: I'm not sure if there's a better way to do implement this.
    # If this gives issues, I can alternatively try...
    #   from dask.distributed import client
    #   client._get_global_client()
    # ... based on https://stackoverflow.com/questions/59070260/

    return client
