# -*- coding: utf-8 -*-

import pytest
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse

from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import (
    get_workflow_types,
    get_list_of_all_workflows,
    get_workflow,
)

ALL_WORKFLOWS = get_list_of_all_workflows()


def test_workflows_view(client):
    response = client.get("/workflows/")
    assert response.status_code == 200
    assertTemplateUsed(response, "workflows/all.html")


@pytest.mark.parametrize("workflow_type", get_workflow_types())
def test_workflows_by_type_view(client, workflow_type):

    # grabs f"/workflows/{workflow_type}/"
    url = reverse(
        "workflows_by_type",
        kwargs={"workflow_type": workflow_type},
    )

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "workflows/by_type.html")


@pytest.mark.django_db
@pytest.mark.parametrize("workflow_name", ALL_WORKFLOWS)
def test_workflow_detail_view(client, workflow_name):

    # BUG: I assume .vasp. in the view for now
    if workflow_name == "restart.simmate.automatic":
        return

    workflow = get_workflow(workflow_name)

    # list view
    # grabs f"/workflows/{type}/{name}/")
    url = reverse(
        "workflow_detail",
        kwargs={
            "workflow_type": workflow.name_project,
            "workflow_name": workflow.name_preset,
        },
    )

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "workflows/detail.html")

    # detail view - found
    # grabs... "/workflows/static-energy/mit/1/"
    # TODO: how should I populate with test data?

    # detail view - not found
    # grabs... "/workflows/static-energy/mit/999/"
    url = reverse(
        "workflow_run_detail",
        kwargs={
            "workflow_type": workflow.name_project,
            "workflow_name": workflow.name_preset,
            "pk": 999,
        },
    )

    response = client.get(url)
    assert response.status_code == 404
    # assertTemplateUsed(response, "workflows/detail_run.html")


# @pytest.mark.parametrize("workflow_name", ALL_WORKFLOWS) # TODO
@pytest.mark.django_db
def test_workflow_submit_view(client, sample_structures, mocker):

    client.login(username="test_user", password="test_password")

    url = reverse(
        "workflow_submit",
        kwargs={
            "workflow_type": "static-energy",
            "workflow_name": "mit",
        },
    )

    # loading blank page
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "workflows/submit.html")

    # grab a test structure to submit
    structure = sample_structures["C_mp-48_primitive"]

    # I don't want to actually run the workflow, so I override the run method
    mocker.patch.object(
        Workflow,
        "run_cloud",
        return_value="example-run-id-1234",
    )

    # submit the form
    response = client.post(
        url,
        {
            "labels": "test_label1",
            # This is just JSON for a NaCl structure
            "structure_json": structure.to_json(),
        },
    )

    assert (
        response.url == "https://cloud.prefect.io/simmate/flow-run/example-run-id-1234"
    )
    Workflow.run_cloud.assert_called_with(
        structure=structure,
        labels=["test_label1"],
        source=None,
        copy_previous_directory=False,
        wait_for_run=False,
        pre_sanitize_structure=False,
        pre_standardize_structure=False,
        # parameters not deserialized yet so these will still be present
        command="",
        directory="",
        is_restart=False,
    )
