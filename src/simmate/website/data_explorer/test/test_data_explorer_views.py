# -*- coding: utf-8 -*-

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed


def test_providers_view(client):
    # grabs f"/data/"
    url = reverse("data_explorer:home")

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "data_explorer/providers_all.html")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "provider_name",
    [
        "AflowPrototype",
        "MatprojStructure",
        "CodStructure",
        "JarvisStructure",
        "OqmdStructure",
    ],
)
def test_workflows_by_type_view(client, provider_name):
    # list view

    # grabs f"/workflows/{workflow_type}/"
    url = reverse(
        "data_explorer:provider",
        kwargs={"provider_name": provider_name},
    )

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "data_explorer/provider.html")

    # detail view
    url = reverse(
        "data_explorer:entry-detail",
        kwargs={
            "provider_name": provider_name,
            "pk": 999,
        },
    )

    response = client.get(url)
    assert response.status_code == 404
    # assertTemplateUsed(response, "data_explorer/entry_detail.html")
