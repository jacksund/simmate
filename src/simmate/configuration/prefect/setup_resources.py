# -*- coding: utf-8 -*-

import os
from pathlib import Path

import yaml

# This must be done BEFORE importing any other dask modules
from simmate.configuration import dask  # loads default cluster settings

from dask.distributed import LocalCluster
import dask_jobqueue

from prefect.agent.local import LocalAgent

from simmate.configuration.prefect.connect_to_dask import set_default_executor

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

# Load our default cluster type, agent name, and agent labels
def load_agent_settings():
    SIMMATE_DIRECTORY = os.path.join(Path.home(), "simmate")
    AGENT_YAML = os.path.join(SIMMATE_DIRECTORY, "prefect_agent.yaml")
    if os.path.exists(AGENT_YAML):
        with open(AGENT_YAML) as file:
            settings = yaml.full_load(file)
    else:
        settings = {}

    # update each entry if it's not set in the yaml file
    default_values = {
        "agent_name": None,
        "agent_labels": [],
        "dask_cluster_type": "Local",
    }
    for key, default_value in default_values.items():
        if not settings.get(key):
            settings[key] = default_value

    # make sure we have a legal cluster type
    if settings["dask_cluster_type"] not in ALLOWED_CLUSTER_TYPES:
        raise Exception(
            f"{settings['dask_cluster_type']} is not an allowed cluster type."
            f"Please choose one of the following: {ALLOWED_CLUSTER_TYPES}"
        )

    return settings


default_agent_settings = load_agent_settings()

# NOTE: if you are using a jobqueue cluster, this function assumes you have
# default values set in a Dask config file.
def run_cluster_and_agent(
    cluster_type=default_agent_settings["dask_cluster_type"],
    agent_name=default_agent_settings["agent_name"],
    agent_labels=default_agent_settings["agent_labels"],
    njobs=None,  # Required for jobqueue-based clusters
    # I include these three options because they are commonly overwritten when
    # setting up clusters. I need to revist this in the future though and consider
    # adding more or just accpeting a general **cluster_kwargs for input
    job_cpu=None,
    job_mem=None,
    walltime=None,
):

    ################# STEP 1: Configure our Dask Cluster. #################

    # check if the user wants to override default settings for the SLURM jobs.
    # Each of these will only be passed to Cluster() if they are set
    cluster_kwargs = {}
    if job_cpu:
        cluster_kwargs["job_cpu"] = job_cpu
    if job_mem:
        cluster_kwargs["job_mem"] = job_mem
    if walltime:
        cluster_kwargs["walltime"] = walltime

    # Start a local cluster with default settings if requested
    if cluster_type == "Local":
        cluster = LocalCluster(n_workers=njobs)

    # otherwise we have a jobqueue cluster
    else:
        # grab the class from the module. It will be named something like PBSCluster
        ClusterClass = getattr(dask_jobqueue, f"{cluster_type}Cluster")
        # Now initialize the cluster using the default Dask config.
        cluster = ClusterClass(**cluster_kwargs)
        if not njobs:
            raise Exception("You must provide nworkers when using a JobQueue cluster")
        cluster.scale(njobs)

    # print some info about the cluster for the user
    print(HEADER_ART)
    print(f"Scheduler is located at {cluster.scheduler.address}")
    print(f"Dashboard is located at {cluster.dashboard_link}")
    print(
        "To view the dashboard via ssh, use the command... \n\t"
        "ssh -N -L 8787:warwulf.net:8787 WarrenLab@warwulf.net"  # TODO: make more general
    )
    # Also if we have a jobqueue, we can display the submit script being used.
    if issubclass(cluster.__class__, dask_jobqueue.JobQueueCluster):
        print("Workers are submitted to SLURM with the following submit.sh...\n")
        print(cluster.job_script())
    else:
        print("Workers are all ran on the local machine.")
    print("\n\n")

    ################# STEP 2: Configure our Dask Cluster. #################

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

    #######################################################################
