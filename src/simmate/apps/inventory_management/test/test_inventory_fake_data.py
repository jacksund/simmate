# -*- coding: utf-8 -*-

from datetime import timedelta

from django.utils import timezone

from simmate.apps.inventory_management.components.dashboard import (
    InventoryDashboardComponent,
)
from simmate.apps.inventory_management.models import (
    Batch,
    Container,
    Molecule,
    Substance,
    UsageLog,
)


def test_inventory_fake_data(fake_data, client):
    counts = fake_data("inventory_management")
    assert counts["inventory_management.Substance"] == Substance.objects.count() > 0
    assert UsageLog.objects.count() > 0

    # molecules are built from SMILES
    assert not Molecule.objects.filter(smiles__isnull=True).exists()

    for substance in Substance.objects.all():
        assert Substance.validate_id(substance.id, substance.check_digit)

    # timestamps are kept (not reset by auto_now) and shifted to the present
    assert UsageLog.objects.order_by("created_at").first().created_at < (
        timezone.now() - timedelta(days=7)
    )
    assert Batch.objects.filter(parent_batches__isnull=False).exists()

    # sequences are reset, so new rows can still be added
    Container.objects.create(amount_units="g")

    now = timezone.now()
    batch_stats = InventoryDashboardComponent.get_batch_stats(now)
    assert batch_stats["nexpired"] > 0
    assert batch_stats["nexpiring"] > 0
    container_stats = InventoryDashboardComponent.get_container_stats()
    assert container_stats["nlow"] > 0
    assert container_stats["nempty"] > 0

    InventoryDashboardComponent._slow_context = None  # shared across tests
    response = client.get("/apps/inventory_management/")
    assert response.status_code == 200
