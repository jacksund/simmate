# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.workflows import views

urlpatterns = [
    #
    # Lists off the different types of workflows (static-energy, relaxation, etc.)
    path(
        route="",
        view=views.all_workflow_types,
        name="workflows",  # kept to shorthand bc it is the workflows homepage
    ),
    #
    # Lists off the different workflows of a given type (e.g. all static-energy)
    path(
        route="<workflow_type>/",
        view=views.workflows_of_given_type,
        name="workflows_of_given_type",
    ),
    #
    # A detailed view of a specific workflow. This page will contain sections
    # about the workflow as well as host actions for submitting and querying
    # new flow runs.
    path(
        route="<workflow_type>/<workflow_app>/<workflow_preset>",
        # view=views.workflow_detail,
        view=views.workflows_of_given_type,
        name="workflow_detail",
    ),
    #
    # Views results for an individual calculation
    # path(
    #     route="<workflow_type>/<workflow_app>/<workflow_preset>/<int:pk>",
    #     view=views.WorkflowAPIViewSet.dynamic_retrieve_view,
    #     name="workflow_run_detail",
    # ),
    #
    # Submit a new calculation
    # path(
    #     route="<workflow_type>/<workflow_app>/<workflow_preset>/submit",
    #     view=views.workflow_submit,
    #     name="workflow_submit",
    # ),
]
