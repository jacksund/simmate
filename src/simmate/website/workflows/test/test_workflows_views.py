# -*- coding: utf-8 -*-

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import (
    get_all_workflow_names,
    get_all_workflow_types,
    get_workflow,
)


def get_workflows_to_test():
    # Some views have not been configured yet, so we
    # remove them from the list of all flows

    all_flow_names = get_all_workflow_names()

    flows_to_test = []
    for workflow_name in all_flow_names:
        workflow = get_workflow(workflow_name)
        if workflow.name_type not in [
            "customized",
            "restart",
            "electronic-structure",
            "structure-prediction",
            "diffusion",
        ]:
            flows_to_test.append(workflow)
    return flows_to_test


ALL_WORKFLOWS = get_workflows_to_test()


def test_workflows_view(client):
    response = client.get("/workflows/")
    assert response.status_code == 200
    assertTemplateUsed(response, "workflows/all.html")


@pytest.mark.parametrize("workflow_type", get_all_workflow_types())
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
@pytest.mark.parametrize("workflow", ALL_WORKFLOWS)
def test_workflow_detail_view(client, workflow):

    # Some views have not been configured yet
    if workflow.name_type in [
        "customized",
        "electronic-structure",
        "structure-prediction",
        "diffusion",
    ]:
        return

    # list view
    # grabs f"/workflows/{type}/{calculator}/{preset}/")
    url = reverse(
        "workflow_detail",
        kwargs={
            "workflow_type": workflow.name_type,
            "workflow_calculator": workflow.name_calculator,
            "workflow_preset": workflow.name_preset,
        },
    )

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "workflows/detail.html")

    # detail view - found
    # grabs... "/workflows/static-energy/vasp/mit/1/"
    # TODO: how should I populate with test data?

    # detail view - not found
    # grabs... "/workflows/static-energy/vasp/mit/999/"
    url = reverse(
        "workflow_run_detail",
        kwargs={
            "workflow_type": workflow.name_type,
            "workflow_calculator": workflow.name_calculator,
            "workflow_preset": workflow.name_preset,
            "pk": 999,
        },
    )

    response = client.get(url)
    assert response.status_code == 404
    # assertTemplateUsed(response, "workflows/detail_run.html")


# TODO: @pytest.mark.parametrize("workflow", ALL_WORKFLOWS)
@pytest.mark.django_db
def test_workflow_submit_view(client, sample_structures, mocker):

    client.login(username="test_user", password="test_password")

    url = reverse(
        "workflow_submit",
        kwargs={
            "workflow_type": "static-energy",  # workflow.name_type
            "workflow_calculator": "vasp",  # workflow.name_calculator
            "workflow_preset": "mit",  # workflow.name_preset
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
            "tags": "test_tag1",
            # This is just JSON for a NaCl structure
            "structure_json": structure.to_json(),
        },
    )

    assert response.status_code == 302  # indicates a redirect URL
    assert (
        response.url == "https://cloud.prefect.io/simmate/flow-run/example-run-id-1234"
    )
    Workflow.run_cloud.assert_called_with(
        structure=structure,
        tags=["test_tag1"],
        compress_output=False,
        wait_for_run=False,
        # parameters not deserialized yet so these will still be present
        command="",
        directory="",
        source=None,
        run_id="",
        is_restart=False,
        standardize_structure="",
        angle_tolerance=None,
        symmetry_precision=None,
    )
