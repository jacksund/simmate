# -*- coding: utf-8 -*-

import os


def set_default_executor(dask_scheduler_address):
    """
    If you want to start a Prefect Agent that uses a specific Dask Cluster for
    all workflow runs, you can run this function before starting your Prefect
    Agent.

    What it does is set two enviornment variables that tell Prefect to default
    all workflows to using a default executor. So this saves us from having to
    repeatedly use this line below when setting ups workflows...
        from prefect.executors import DaskExecutor
        workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

    After you run this command, you can start your Prefect Agent as usual...
        from prefect.agent.local import LocalAgent
        agent = LocalAgent(name="ExampleAgent")
        agent.start()
    """

    # All workflows should be pointed to the Dask cluster as the default Executor.
    # We can grab the Dask scheduler's address using the cluster object from above.
    # For the master node, this address is "tcp://152.2.172.72:8786"
    os.environ.setdefault(
        "PREFECT__ENGINE__EXECUTOR__DEFAULT_CLASS", "prefect.executors.DaskExecutor"
    )
    os.environ.setdefault(
        "PREFECT__ENGINE__EXECUTOR__DASK__ADDRESS", dask_scheduler_address
    )
