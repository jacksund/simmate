# -*- coding: utf-8 -*-

import pytest
from pytest_django.asserts import assertTemplateNotUsed, assertTemplateUsed


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
    # signed-out users only see the app summaries and a sign-in prompt
    assertTemplateNotUsed(response, "core/dashboard/widget_frame.html")
    assert "Sign in to see your dashboard" in response.content.decode()


@pytest.mark.django_db
def test_dashboard_view_signed_in(admin_client):
    response = admin_client.get("/dashboard/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core/dashboard/widget_frame.html")
    assertTemplateUsed(response, "core/dashboard/widget_catalog.html")
    for widget in response.context["main_widgets"] + response.context["side_widgets"]:
        assertTemplateUsed(response, widget["template"])


@pytest.mark.django_db
def test_apps_view(client):
    response = client.get("/apps/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core/apps.html")
    # app-specific cards plus the built-in static cards
    assertTemplateUsed(response, "compute_management/app_card.html")
    assertTemplateUsed(response, "core/app_cards/data_catalogs.html")
    assertTemplateUsed(response, "core/app_cards/workflows_hub.html")
    content = response.content.decode()
    assert "Scientific Data Catalogs" in content
    assert "Workflows Hub" in content
    assert 'href="compute/"' in content


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
def test_project_management_app_view(client):
    response = client.get("/apps/project_management/")
    assert response.status_code == 200
    assertTemplateUsed(response, "project_management/home.html")


@pytest.mark.django_db
def test_lab_automation_app_view(client):
    response = client.get("/apps/lab_automation/")
    assert response.status_code == 200
    assertTemplateUsed(response, "lab_automation/home.html")
