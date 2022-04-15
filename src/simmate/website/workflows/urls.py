# -*- coding: utf-8 -*-

from django.urls import path

from simmate.website.workflows import views

urlpatterns = [
    #
    # Lists off the different types of calculations
    path(
        route="",
        view=views.workflows_all,
        name="workflows",
    ),
    #
    # Lists off the different workflows of a given type
    path(
        route="<workflow_type>/",
        view=views.workflows_by_type,
        name="workflows_by_type",
    ),
    #
    # A detailed view of a specific workflow. This page will contain sections
    # about the workflow as well as host actions for submitting and querying
    # new flow runs.
    path(
        route="<workflow_type>/<workflow_name>/",
        view=views.WorkflowAPIViewSet.dynamic_list_view,
        name="workflow_detail",
    ),
    #
    # Views results for an individual calculation
    path(
        route="<workflow_type>/<workflow_name>/<int:pk>",
        view=views.WorkflowAPIViewSet.dynamic_retrieve_view,
        name="workflow_run_detail",
    ),
    #
    # Submit a new calculation
    path(
        route="<workflow_type>/<workflow_name>/submit",
        view=views.workflow_submit,
        name="workflow_submit",
    ),
]
