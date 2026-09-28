# -*- coding: utf-8 -*-

import pytest
from pytest_django.asserts import assertTemplateUsed


@pytest.mark.django_db
def test_home_view(client):
    # test initial view
    response = client.get("/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core/home.html")

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


@pytest.mark.django_db
def test_contact_view(client):
    response = client.get("/contact/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core/contact.html")


@pytest.mark.django_db
def test_about_view(client):
    response = client.get("/about/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core/about.html")


@pytest.mark.django_db
def test_dashboard_view(client):
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core/dashboard.html")


@pytest.mark.django_db
def test_apps_view(client):
    response = client.get("/apps/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core/apps.html")


@pytest.mark.django_db
def test_compute_app_view(client):
    response = client.get("/apps/compute/")
    assert response.status_code == 200
    assertTemplateUsed(response, "compute_management/home.html")


@pytest.mark.django_db
def test_inventory_management_app_view(client):
    response = client.get("/apps/inventory_management/")
    assert response.status_code == 200
    assertTemplateUsed(response, "inventory_management/home.html")


@pytest.mark.django_db
def test_lab_automation_app_view(client):
    response = client.get("/apps/lab_automation/")
    assert response.status_code == 200
    assertTemplateUsed(response, "lab_automation/home.html")
