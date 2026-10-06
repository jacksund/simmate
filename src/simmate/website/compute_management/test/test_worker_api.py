# -*- coding: utf-8 -*-

import pytest

from simmate.compute.api import views

CHECK_URL = "/apps/compute/workers/check/"


@pytest.mark.django_db
def test_check_worker_access_requires_login(client):
    response = client.get(CHECK_URL)
    assert response.status_code == 302  # to the login page


@pytest.mark.django_db
@pytest.mark.parametrize("allowed", [True, False])
def test_check_worker_access(client, django_user_model, monkeypatch, allowed):
    user = django_user_model.objects.create_user(username="worker", password="pw")
    client.force_login(user)
    monkeypatch.setattr(views, "check_worker_permissions", lambda user: allowed)

    response = client.get(CHECK_URL)
    assert response.status_code == 200
    assert response.json() == {"username": "worker", "can_run_workers": allowed}

    # it must never hand out (or claim) work
    assert client.post(CHECK_URL).status_code == 405
