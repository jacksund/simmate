# -*- coding: utf-8 -*-

from simmate.apps.project_management.models import Project, Transaction, Wallet


def test_project_fake_data(fake_data):
    counts = fake_data("project_management")
    assert counts["project_management.Project"] == Project.objects.count() > 0
    assert Transaction.objects.count() > 0

    zeus = Project.objects.get(name="Zeus")
    assert zeus.child_projects.count() == zeus.num_child_projects_recursive == 2
    assert zeus.leaders.exists()

    # user wallets come from a signal when the users are created
    assert Wallet.objects.filter(user__username="chemist1", wallet_type="user").exists()
    assert (
        Wallet.objects.filter(wallet_type="project").count() == Project.objects.count()
    )

    # balances match the completed transactions
    Wallet.validate_ledger()
    assert not Wallet.objects.filter(wallet_type="project", usdc_balance__lt=0).exists()

    # sequences are reset, so new rows can still be added
    Wallet.objects.create(wallet_type="project")
