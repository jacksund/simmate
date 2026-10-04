# -*- coding: utf-8 -*-

from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from simmate.apps.project_management.components.dashboard import (
    ProjectDashboardComponent,
)
from simmate.apps.project_management.models import Project, Wallet
from simmate.config import settings


@pytest.mark.django_db
def test_dashboard(client, monkeypatch):
    now = timezone.now()
    leader = User.objects.create(username="leader")
    member = User.objects.create(username="member")

    zeus = Project.objects.create(name="Zeus", status="Active", is_top_level=True)
    zeus.leaders.add(leader)
    zeus.members.add(leader, member)
    athena = Project.objects.create(
        name="Athena", status="Requires Update", parent_project=zeus
    )
    athena.leaders.add(leader)
    athena.members.add(member)
    apollo = Project.objects.create(name="Apollo", status="Active", is_top_level=True)
    apollo.leaders.add(member)
    # stale and without leaders
    hermes = Project.objects.create(name="Hermes", status="Active")
    Project.objects.filter(id=hermes.id).update(updated_at=now - timedelta(days=400))
    Project.objects.create(name="Hestia", status="Under Review")

    stats = ProjectDashboardComponent.get_project_stats(now)
    assert stats["nrequires_update"] == 1
    assert stats["nstale"] == 1
    assert stats["nreview"] == 1
    assert stats["nno_leaders"] == 2  # not inflated by the leaders join

    alerts = ProjectDashboardComponent.get_alerts(now, stats)
    assert len(alerts) == 4
    for alert in alerts:
        response = client.get(alert["url"])
        assert response.status_code == 200, alert["url"]

    projects = ProjectDashboardComponent.get_project_tree()
    assert {p.name for p in projects} == {"Zeus", "Apollo", "Hermes", "Hestia"}
    zeus_entry = next(p for p in projects if p.name == "Zeus")
    assert [c.name for c in zeus_entry.children] == ["Athena"]
    assert zeus_entry.nmembers == 2 and zeus_entry.nleaders == 1

    my_projects = ProjectDashboardComponent.get_my_projects(member)
    roles = {p.name: p.role for p in my_projects}
    assert roles == {"Zeus": "Member", "Athena": "Member", "Apollo": "Leader"}

    response = client.get("/apps/project_management/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Needs Attention" in content
    assert "Labels for organizing project data" in content
    assert "Zeus" in content
    assert "Recent Transactions" not in content

    # finance panels
    monkeypatch.setitem(settings.final_settings["website"], "show_finances", True)
    treasury = Wallet.objects.create(wallet_type="simmate-treasury")
    zeus_wallet = Wallet.objects.create(wallet_type="project", project=zeus)
    treasury.send(
        to_wallet=zeus_wallet, usdc_amount=100, status="Pending", sending_user=leader
    )
    stats.update(ProjectDashboardComponent.get_finance_stats(now))
    assert stats["npending"] == 1
    alerts = ProjectDashboardComponent.get_alerts(now, stats, show_finances=True)
    assert len(alerts) == 5
    for alert in alerts:
        response = client.get(alert["url"])
        assert response.status_code == 200, alert["url"]

    client.force_login(member)
    response = client.get("/apps/project_management/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Recent Transactions" in content
    assert "USDC and token balances" in content
    assert "My Projects" in content
