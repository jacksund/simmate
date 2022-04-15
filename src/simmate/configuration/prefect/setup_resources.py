# -*- coding: utf-8 -*-

import os
from pathlib import Path
import yaml
from typing import List

from prefect.agent.local import LocalAgent

from simmate.configuration.prefect.connect_to_dask import set_default_executor
from simmate.configuration.dask.setup_cluster import run_cluster


def load_agent_settings() -> dict:
    """
    Load our default cluster type, agent name, and agent labels. This is loaded
    from the file `prefect_agent.yaml`.
    """

    SIMMATE_DIRECTORY = os.path.join(Path.home(), "simmate")
    AGENT_YAML = os.path.join(SIMMATE_DIRECTORY, "prefect_agent.yaml")
    if os.path.exists(AGENT_YAML):
        with open(AGENT_YAML) as file:
            settings = yaml.full_load(file)
    else:
        settings = {}

    # update each of these entries if it's not set in the yaml file
    default_values = {
        "agent_name": None,
        "agent_labels": [],
        "dask_cluster_type": "Local",
    }
    for key, default_value in default_values.items():
        if not settings.get(key):
            settings[key] = default_value

    return settings


DEFAULT_AGENT_SETTINGS = load_agent_settings()


def run_cluster_and_agent(
    cluster_type: str = DEFAULT_AGENT_SETTINGS["dask_cluster_type"],
    agent_name: str = DEFAULT_AGENT_SETTINGS["agent_name"],
    agent_labels: List[str] = DEFAULT_AGENT_SETTINGS["agent_labels"],
    **cluster_kwargs,
):

    # start our dask cluster
    cluster = run_cluster(
        cluster_type=cluster_type,
        **cluster_kwargs,
    )

    # We want Prefect to use our Dask Cluster to run all of the workflow tasks. To
    # tell Prefect to do this, we wrote a helper function (set_default_executor) that
    # ships with Simmate.
    set_default_executor(cluster.scheduler.address)

    agent = LocalAgent(
        name=agent_name,
        labels=agent_labels,
        hostname_label=False,
    )

    # Now we can start the Prefect Agent which will run and search for jobs and then
    # submit them to our Dask cluster.
    agent.start()
    # NOTE: this line will run endlessly unless you set a timelimit in the LocalAgent above
