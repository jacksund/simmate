# -*- coding: utf-8 -*-

import pytest
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse


def test_providers_view(client):

    # grabs f"/third-parties/"
    url = reverse("third_parties:home")

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "third_parties/providers_all.html")


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
        "third_parties:provider",
        kwargs={"provider_name": provider_name},
    )

    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, "third_parties/provider.html")

    # detail view
    url = reverse(
        "third_parties:entry-detail",
        kwargs={
            "provider_name": provider_name,
            "pk": 999,
        },
    )

    response = client.get(url)
    assert response.status_code == 404
    # assertTemplateUsed(response, "third_parties/entry_detail.html")
