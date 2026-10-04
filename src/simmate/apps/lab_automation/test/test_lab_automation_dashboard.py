# -*- coding: utf-8 -*-

import pytest

from simmate.apps.lab_automation.components import (
    AirQualityComponent,
    AmbientTempComponent,
    Hotplate2StirComponent,
    Hotplate2TempComponent,
    HotplateStirComponent,
    HotplateTempComponent,
    HumidityComponent,
    LabDashboardComponent,
)
from simmate.apps.lab_automation.components.dashboard import TASKS

SENSORS = [
    AmbientTempComponent,
    HumidityComponent,
    AirQualityComponent,
    HotplateTempComponent,
    HotplateStirComponent,
    Hotplate2TempComponent,
    Hotplate2StirComponent,
]


def test_alerts():
    messages = " ".join(a["message"] for a in LabDashboardComponent.get_alerts())
    for task in TASKS["failed"]:
        assert task["name"] in messages


@pytest.mark.parametrize("sensor", SENSORS)
def test_sensor(sensor):
    for _ in range(3):
        x, y = sensor.get_latest_data()
    assert len(x) == len(y) >= 3
    if sensor.value_range:
        assert all(sensor.value_range[0] <= v <= sensor.value_range[1] for v in y)

    status, theme = sensor().get_status(sensor.target)
    assert (status, theme) == ("nominal", "success")


def test_sensor_histories_are_separate():
    assert HotplateTempComponent.history_y is not Hotplate2TempComponent.history_y


@pytest.mark.django_db
def test_dashboard_page(client):
    response = client.get("/apps/lab_automation/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Lab Automation" in content
    assert "Task Board" in content
    assert "People and robots working in the lab" in content
    assert "Hotplate 2" in content
    assert "Ambient Temp" in content
