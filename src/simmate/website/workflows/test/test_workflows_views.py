# -*- coding: utf-8 -*-

import pytest
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse
from simmate.workflow_engine import Workflow


def test_workflows_view(client):
    response = client.get("/workflows/")
    assert response.status_code == 200
    assertTemplateUsed("workflows/all.html")


def test_workflows_by_type_view(client):
    response = client.get("/workflows/static-energy/")
    assert response.status_code == 200
    assertTemplateUsed("workflows/by_type.html")

    response = client.get("/workflows/relaxation/")
    assert response.status_code == 200
    assertTemplateUsed("workflows/by_type.html")


@pytest.mark.django_db
def test_workflow_detail_view(client):

    # list view
    response = client.get("/workflows/static-energy/mit/")
    assert response.status_code == 200
    assertTemplateUsed("workflows/detail.html")

    # detail view - found
    # grabs... "/workflows/static-energy/mit/1/"
    # url = reverse(
    #     "workflow_run_detail",
    #     kwargs={
    #         "workflow_type": "static-energy",
    #         "workflow_name": "mit",
    #         "workflow_run_id": 1,
    #     },
    # )
    # response = client.get(url)
    # assert response.status_code == 200
    # assertTemplateUsed("workflows/detail_run.html")

    # detail view - not found
    # grabs... "/workflows/static-energy/mit/999/"
    url = reverse(
        "workflow_run_detail",
        kwargs={
            "workflow_type": "static-energy",
            "workflow_name": "mit",
            "workflow_run_id": 999,
        },
    )
    response = client.get(url)
    assert response.status_code == 404
    assertTemplateUsed("workflows/detail_run.html")


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
    assertTemplateUsed("workflows/submit.html")

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
        use_previous_directory=False,
        wait_for_run=False,
    )
