# -*- coding: utf-8 -*-

import pytest
from pytest_django.asserts import assertTemplateUsed


@pytest.mark.django_db
def test_home_view(client):

    # test initial view
    response = client.get("/")
    assert response.status_code == 200
    assertTemplateUsed(response, "home/home.html")

    # test submission of the form
    response = client.post(
        "/",
        {
            "chemical_system": "Y-F-C",
            "materials_project": True,
            "jarvis": True,
        },
    )
    assert response.status_code == 200


def test_extras_view(client):
    response = client.get("/extras/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core_components/extras.html")


def test_contact_view(client):
    response = client.get("/contact/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core_components/contact.html")


def test_about_view(client):
    response = client.get("/about/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core_components/about.html")
