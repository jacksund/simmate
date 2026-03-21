# -*- coding: utf-8 -*-

import pytest
from django.contrib.auth.models import User
from pytest_django.asserts import assertTemplateUsed

from simmate.website.core.models import Notification


@pytest.mark.django_db
def test_notification_model():
    user = User.objects.create_user(username="testuser", password="password")
    notification = Notification.create_notification(
        user=user,
        message="Test Notification",
        notification_type="test_type",
        target_url="/test-url/",
    )
    assert notification.user == user
    assert notification.message == "Test Notification"
    assert notification.notification_type == "test_type"
    assert notification.is_read == False


@pytest.mark.django_db
def test_profile_notifications(client):
    user = User.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")

    # Create unread notifications
    Notification.create_notification(
        user=user, message="Message 1", notification_type="workflow_update"
    )
    Notification.create_notification(
        user=user, message="Message 2", notification_type="workflow_update"
    )
    Notification.create_notification(
        user=user, message="Alert 1", notification_type="system_alert"
    )

    response = client.get("/accounts/profile/")
    assert response.status_code == 200
    assertTemplateUsed(response, "account/profile.html")

    # Check if messages are present
    assert b"Message 1" in response.content
    assert b"Message 2" in response.content
    assert b"Alert 1" in response.content

    # Check if grouped counts are correct (2 workflow updates, 1 system alert)
    assert b"2</span>" in response.content
    assert b"1</span>" in response.content

    # Check navbar badge (total 3 unread)
    assert b"3" in response.content


@pytest.mark.django_db
def test_mark_as_read(client):
    user = User.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")

    Notification.create_notification(
        user=user, message="Unread Message", notification_type="test"
    )

    assert user.notifications.filter(is_read=False).count() == 1

    response = client.get("/accounts/profile/mark-as-read/")
    assert response.status_code == 302  # redirect to profile

    assert user.notifications.filter(is_read=False).count() == 0
