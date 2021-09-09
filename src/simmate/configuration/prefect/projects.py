# -*- coding: utf-8 -*-

from prefect import Client


def build():

    # grab the Prefect client
    client = Client()

    # BUG: for now we assume we are in the correct tenant. If not, we'd need to run:
    #   client.login_to_tenant(tenant_slug='a-tenant-slug')

    # build the Simmate projects
    project_id = client.create_project(project_name="Simmate-Relaxation")

    # grab all of the workflows that need to be registered
    from simmate.workflows.relaxation.all import mit_relaxation

    workflows = [
        mit_relaxation,
        # TODO: I'll add more here in the future
    ]

    # register the workflows with the proper projects
    for workflow in workflows:
        workflow_id = workflow.register(
            project_name="Simmate-Relaxation",
            set_schedule_active=False,
        )

    # TODO: will I need to store the project or workflow IDs? Maybe inside
    # the /.simmate/prefect folder? Or maybe even the /.prefect folder?
    return project_id, workflow_id


def delete():

    # grab the Prefect client
    client = Client()

    # delete all of the Simmate projects
    # BUG: if there's too much data in any of these projects, then the command
    # may time-out. In that case, I may need to delete some flow runs manually
    # before I can delete the project.
    try:
        is_successful = client.delete_project(project_name="Simmate-Relaxation")
    except ValueError:
        # an error will be raised if the project isn't found -- so if it doesn't
        # exist, it's already deleted. We can just move on in this case.
        is_successful = True
        pass

    # BUG advisory
    print(
        "Deleting projects in Prefect Cloud is a 'lazy' mutation. This means the "
        "project is only hidden initally and the deletion could take a few minutes "
        "to complete in Prefect's backend. Therefore, you'll need to wait some "
        "time before trying to recreate your projects with build(). 1 minute should "
        "be plenty of time, but their team says this can take as much as 30+ min."
    )

    return is_successful


# BUG: calling delete and then build back-to-back causes errors because delete
# is a lazy operation. Therefore, users need to "sleep here for some time"
# def reset():
#     # reseting just involves deleting all projects and then recreating them
#     # OPTIMIZE: both of these functions connect to a client. I believe it would
#     # be faster to just connect once.
#     delete()
#     build()
