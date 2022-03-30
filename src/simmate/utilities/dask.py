# -*- coding: utf-8 -*-

from dask.distributed import Client, get_client, wait, TimeoutError

from typing import List, Callable


def get_dask_client(**kwargs):
    """
    This is a convenience utility that grabs the client for the local Dask cluster
    if it exists -- and if not, creates a new cluster and returns the client for
    it.

    Paramters
    ---------

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

    # OPTIMIZE: I'm not sure if there's a better way to do implement this.
    # If this gives issues, I can alternatively try...
    #   from dask.distributed import client
    #   client._get_global_client()
    # ... based on https://stackoverflow.com/questions/59070260/

    return client


def dask_batch_submit(
    function: Callable,
    args_list: List[dict],
    batch_size: int,
    batch_timeout: float = None,
):
    """
    Given a function and a list of inputs that should be iterated over, this
    submits all inputs to a Dask local cluster in batches.

    This function has very specific use-cases, such as when we are submitting
    >100,000 tasks and each task is unstable / writing to the database. Therefore,
    you should test out Dask normally before trying this utility. Always give
    preference to Dask's `client.map` method over this utility.

    Parameters
    ----------
    - `function`:
        Function that each kwargs entry should be called with.
    - `args_list`:
        A list of parameters that will each be submitted to function via
        function(*args).
    - `batch_size`:
        The number of calls to submit at a time. No new jobs will be
        submitted until the entire preceeding batch completes.
    - `batch_timeout`:
        The timelimit to wait for any given batch before cancelling the remaining
        runs. No error will be raised when jobs are cancelled. The default is
        no timelimit.
    """
    # TODO: I'd like to support a list of kwargs as well
    # TODO: should I add an option to return the results?

    # grab the Dask client
    client = get_dask_client()

    # Iterate through our inputs and submit them to the Dask cluster in batches
    for i in range(0, len(args_list), batch_size):
        chunk = args_list[i : i + batch_size]
        futures = client.map(
            function,
            chunk,
            pure=False,
        )
        try:
            wait(futures, timeout=batch_timeout)
        except TimeoutError:
            client.cancel(futures)
