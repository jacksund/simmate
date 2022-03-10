# -*- coding: utf-8 -*-

from prefect import Client


def build():

    # grab the Prefect client
    client = Client()

    # BUG: for now we assume we are in the correct tenant. If not, we'd need to run:
    #   client.login_to_tenant(tenant_slug='a-tenant-slug')

    # grab all of the workflows that need to be registered
    from simmate.workflows.utilities import get_list_of_all_workflows, get_workflow

    # Load all workflows
    workflow_names = get_list_of_all_workflows()
    workflows = [get_workflow(name) for name in workflow_names]

    # Iterate through and grab all the unique Project names. The brackets here
    # make this return as a set
    project_names = {workflow.project_name for workflow in workflows}

    # build each of the projects
    for project_name in project_names:
        project_id = client.create_project(project_name=project_name)
    # register the workflows with the proper projects
    for workflow in workflows:
        workflow_id = workflow.register(
            project_name=workflow.project_name,
            set_schedule_active=False,
        )
    # TODO: will I need to store the project or workflow IDs? Maybe inside
    # the /simmate/prefect folder? Or maybe even the /.prefect folder?
    # I could also return a list of what's been done.


def delete():

    # grab the Prefect client
    client = Client()

    # query for a list of projects that start with "Simmate-"
    # BUG: I delete all projects for now. I need to update this query to just
    # Simmate projects
    query = "query {project {name}}"
    result = client.graphql(query)
    project_names = [p["name"] for p in result["data"]["project"]]

    # delete all of the Simmate projects
    # BUG: if there's too much data in any of these projects, then the command
    # may time-out. In that case, I may need to delete some flow runs manually
    # before I can delete the project.
    for project_name in project_names:
        try:
            is_successful = client.delete_project(project_name=project_name)
        except ValueError:
            # an error will be raised if the project isn't found -- so if it doesn't
            # exist, it's already deleted. We can just move on in this case.
            is_successful = True
            pass

    # In the scenario we already deleted everything, just say we were successful
    if not project_names:
        is_successful = True

    # BUG advisory
    print(
        "WARNING: Deleting projects in Prefect Cloud is a 'lazy' mutation. This means the "
        "project is only hidden initially and the deletion could take a few minutes "
        "to complete in Prefect's backend. Therefore, you'll need to wait some "
        "time before trying to recreate your projects with build(). 1 minute should "
        "be plenty of time, but the Prefect team says this can take as much as 30+ min."
    )

    return is_successful


# BUG: calling delete and then build back-to-back causes errors because delete
# is a lazy operation. Therefore, users need to "sleep here for some time"
# def reset():
#     # reseting just involves deleting all projects and then recreating them
#     delete()
#     build()
