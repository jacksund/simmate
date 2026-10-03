# -*- coding: utf-8 -*-

from django.utils import timezone

from simmate.compute import SimmateExecutor, SimmateWorker, WorkItem
from simmate.website.compute_management.components.dashboard import (
    ComputeDashboardComponent,
)


def test_compute_fake_data(fake_data, client):
    counts = fake_data("compute_management")
    assert counts["compute_management.WorkItem"] == WorkItem.objects.count() > 0

    # binary columns are kept
    item = WorkItem.objects.filter(status="E").first()
    assert "Error" in ComputeDashboardComponent.get_error_messages([item.id])[item.id]

    # dates are shifted so that workers have fresh (or stale) heartbeats
    assert SimmateWorker.get_active().count() == 4
    assert SimmateWorker.get_stale().count() == 2

    stats = SimmateExecutor.get_stats()
    assert stats["npending"] and stats["nrunning"] and stats["nrunning_long"]
    active_tags = [w.tags for w in SimmateWorker.get_active()]
    assert ComputeDashboardComponent.get_unserved_queues(active_tags)

    # every finished item ran on a worker that was alive at the time
    for item in WorkItem.objects.filter(status="F").select_related("worker"):
        assert item.worker.created_at <= item.started_at < item.updated_at
        assert item.updated_at <= item.worker.updated_at
    assert WorkItem.objects.order_by("created_at").first().created_at < (
        timezone.now() - timezone.timedelta(days=20)
    )

    ComputeDashboardComponent._slow_context = None  # shared across tests
    response = client.get("/apps/compute/")
    assert response.status_code == 200
