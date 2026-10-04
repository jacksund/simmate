# -*- coding: utf-8 -*-

from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from simmate.apps.inventory_management.components.dashboard import (
    InventoryDashboardComponent,
    format_compact,
)
from simmate.apps.inventory_management.models import (
    Batch,
    Container,
    StorageLocation,
    Substance,
    UsageLog,
)


def test_format_compact():
    assert format_compact(1_280) == "1,280"
    assert format_compact(3_400_000_000) == "3.4B"
    assert format_compact(2_000_000_000_000) == "2T"


@pytest.mark.django_db
def test_dashboard(client):
    now = timezone.now()
    user = User.objects.create(username="chemist")
    freezer = StorageLocation.objects.create(
        name="Freezer 1", storage_type="freezer", temperature_celsius=-20
    )
    substance = Substance.objects.create(id="BCD-012-3456", common_name="DMSO")

    expired = Batch.objects.create(
        is_mixture=False,
        substance=substance,
        is_depleted=False,
        expiration_date=now - timedelta(days=2),
    )
    expiring = Batch.objects.create(
        is_mixture=False,
        substance=substance,
        is_depleted=False,
        expiration_date=now + timedelta(days=10),
    )
    Batch.objects.create(is_mixture=False, substance=substance, is_depleted=False)

    low = Container.objects.create(
        batch=expired,
        location=freezer,
        initial_amount=100,
        current_amount=5,
        amount_units="g",
        is_depleted=False,
    )
    Container.objects.create(
        batch=expired,
        initial_amount=100,
        current_amount=0,
        amount_units="g",
        is_depleted=False,
    )
    Container.objects.create(
        batch=expiring,
        location=freezer,
        initial_amount=10,
        current_amount=10,
        amount_units="g",
        is_depleted=False,
    )
    UsageLog.objects.create(source_container=low, user=user, amount_removed=95)

    batch_stats = InventoryDashboardComponent.get_batch_stats(now)
    assert batch_stats["nbatches"] == 3  # not inflated by the containers join
    assert batch_stats["nexpired"] == 1
    assert batch_stats["nexpiring"] == 1
    assert batch_stats["nunstored"] == 1

    container_stats = InventoryDashboardComponent.get_container_stats()
    assert container_stats["nlow"] == 1
    assert container_stats["nempty"] == 1
    assert container_stats["nunlocated"] == 1

    alerts = InventoryDashboardComponent.get_alerts(
        now, stats={**batch_stats, **container_stats}
    )
    assert len(alerts) == 6
    for alert in alerts:
        response = client.get(alert["url"])
        assert response.status_code == 200, alert["url"]

    locations = InventoryDashboardComponent.get_storage_locations()
    assert locations[0].ncontainers == 2 and locations[0].is_cold

    expiring_batches = InventoryDashboardComponent.get_expiring_batches(now)
    assert [b.id for b in expiring_batches] == [expired.id, expiring.id]

    InventoryDashboardComponent._slow_context = None  # shared across tests
    response = client.get("/apps/inventory_management/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Needs Attention" in content
    assert "Storage Locations" in content
    assert "BCD-012-3456" in content
    assert "Freezer 1" in content
