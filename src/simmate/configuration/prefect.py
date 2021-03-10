# -*- coding: utf-8 -*-


from prefect import Client


def build_projects():

    # grab the Prefect client
    client = Client()

    # BUG: for now we assume we are in the correct tenant. If not, we'd need to run:
    #   client.login_to_tenant(tenant_slug='a-tenant-slug')

    # build the Simmate projects

    project_id = client.create_project(project_name="Simmate-Diffusion")

    # register the workflows with the proper projects
    # OPITIMIZE: it would nice to have...
    #   from simmate.workflows.diffusion import workflows

    from simmate.workflows.diffusion.add_structure import (
        workflow as add_structure_workflow,
    )
    from simmate.workflows.diffusion.find_paths import workflow as find_paths_workflow
    from simmate.workflows.diffusion.empirical_measures import (
        workflow as empirical_measures_workflow,
    )
    from simmate.workflows.diffusion.vaspcalc_a import workflow as a_workflow

    workflows = [
        add_structure_workflow,
        find_paths_workflow,
        empirical_measures_workflow,
        a_workflow,
    ]

    for workflow in workflows:
        pass
        # alternatively I could use client.register(workflow)
        workflow_id = workflow.register(project_name="Simmate-Diffusion")

    # TODO: will I need to store the project or workflow IDs? Maybe inside
    # the /.simmate/prefect folder? Or maybe even the /.prefect folder?
    return project_id, workflow_id


def delete_projects():

    # grab the Prefect client
    client = Client()

    # delete all of the Simmate projects
    # BUG: if there's too much data in any of these projects, then the command
    # may time-out. In that case, I may need to delete some flow runs manually
    # before I can delete the project.
    is_successful = client.delete_project(project_name="Simmate-Diffusion")

    return is_successful


def reset_projects():

    # OPTIMIZE: both of these functions connect to a client. I believe it would
    # be fast to just connect once.
    # reseting just involves deleting all projects and then recreating them
    delete_projects()
    build_projects()


def setup_warwulf_cluster_and_agent():
    """
    from simmate.configuration.prefect import setup_warwulf_cluster_and_agent
    setup_warwulf_cluster_and_agent()

    ------SUBMIT.SH------
    #!/bin/bash

    #SBATCH --job-name=prefect_agent
    #SBATCH --output=slurm.out
    #SBATCH --nodes=1
    #SBATCH --ntasks=1
    #SBATCH --cpus-per-task 1
    #SBATCH --partition=p1
    #SBATCH --time=400-00:00

    # Load modules
    module load intel
    module load impi
    module load vasp

    # set python env
    #conda activate jacks_env

    # run Prefect
    python prefect_agent.py
    """

    from simmate.configuration.dask.warwulf import setup_cluster

    cluster = setup_cluster()

    from prefect.agent.local import LocalAgent

    agent = LocalAgent(
        name="WarWulf",
        # max_polls=1,
        labels=["DESKTOP-PVN50G5"]
        # no_cloud_logs=True
    )
    agent.start()
