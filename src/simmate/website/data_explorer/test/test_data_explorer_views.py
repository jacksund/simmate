# -*- coding: utf-8 -*-

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed


def test_providers_view(client):
    # grabs f"/data/"
    url = reverse("data_explorer:home")

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "data_explorer/home.html")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "table_name",
    [
        "AflowPrototype",
        "MatprojStructure",
        "CodStructure",
        "JarvisStructure",
        "OqmdStructure",
    ],
)
def test_workflows_by_type_view(client, table_name):
    # list view

    # grabs f"/workflows/{workflow_type}/"
    url = reverse(
        "data_explorer:table",
        kwargs={"table_name": table_name},
    )

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "data_explorer/table.html")

    # detail view
    url = reverse(
        "data_explorer:table-entry",
        kwargs={
            "table_name": table_name,
            "table_entry_id": 999,
        },
    )

    response = client.get(url)
    assert response.status_code == 404
    # assertTemplateUsed(response, "data_explorer/table_entry.html")
