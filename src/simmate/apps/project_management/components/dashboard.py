# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.urls import reverse
from django.utils import timezone

from simmate.config import settings
from simmate.website.htmx.components import HtmxComponent

from ..models import Project, Transaction, Wallet

STALE_AFTER = timedelta(days=365)
"""
Active projects without any updates in this window are flagged as stale (see
the `Project.status` docs for the 12-month rule).
"""

STATUS_THEMES = {
    "Active": "success",
    "Under Review": "info",
    "Requires Update": "warning",
    "Inactive": "secondary",
    "Staged for Deletion": "danger",
}
"""
The bootstrap color used for each `Project.status` option.
"""

TRANSACTION_STATUS_THEMES = {
    "Complete": "success",
    "Pending": "warning",
    "Under Review": "info",
    "Canceled": "secondary",
    "Denied": "danger",
    "Failed": "danger",
}
"""
The bootstrap color used for each `Transaction.status` option.
"""

FAILED_WINDOW = timedelta(days=7)
"""
Failed transactions within this window are flagged on the dashboard.
"""

PENDING_STATUSES = ["Pending", "Under Review"]
"""
Transaction statuses that still need someone to act on them.
"""

CATALOGS = [
    # (table, title, description, icon, is_finance)
    (
        "Project",
        "Projects",
        "Project goals, teams, and sub-projects",
        "bi-kanban text-success",
        False,
    ),
    (
        "Tag",
        "Tags",
        "Labels for organizing project data",
        "bi-tags text-primary",
        False,
    ),
    (
        "Wallet",
        "Wallets",
        "USDC and token balances for users and projects",
        "bi-wallet2 text-warning",
        True,
    ),
    (
        "Transaction",
        "Transactions",
        "Funding, transfers, payments, and refunds",
        "bi-arrow-left-right text-info",
        True,
    ),
]


class ProjectDashboardComponent(HtmxComponent):
    """
    Project dashboard showing project health, items that need attention
    (stale projects, projects without leaders, etc.), the project tree, and
    the signed-in user's projects. Wallet and transaction panels are only
    shown when `settings.website.show_finances` is True.
    """

    template_name = "project_management/dashboard.html"

    refresh_interval = "60s"

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_context(self):
        ctx = super().get_context()
        now = timezone.now()
        show_finances = settings.website.show_finances

        stats = self.get_project_stats(now)
        if show_finances:
            stats.update(self.get_finance_stats(now))

        ctx.update(
            last_updated=now,
            show_finances=show_finances,
            alerts=self.get_alerts(now, stats, show_finances),
            projects=self.get_project_tree(),
            disciplines=self.get_disciplines(),
            my_projects=self.get_my_projects(getattr(self.request, "user", None)),
            recent_transactions=(
                self.get_recent_transactions() if show_finances else []
            ),
            catalogs=[
                dict(table=table, title=title, description=description, icon=icon)
                for table, title, description, icon, is_finance in CATALOGS
                if show_finances or not is_finance
            ],
        )
        return ctx

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    @staticmethod
    def get_project_stats(now: datetime) -> dict:
        """
        Counts projects by their status and leadership.
        """
        leads = Project.leaders.through.objects
        return Project.objects.aggregate(
            nreview=Count("id", filter=Q(status="Under Review")),
            nrequires_update=Count("id", filter=Q(status="Requires Update")),
            nstaged=Count("id", filter=Q(status="Staged for Deletion")),
            nstale=Count(
                "id", filter=Q(status="Active", updated_at__lt=now - STALE_AFTER)
            ),
            # Exists (rather than a join) avoids duplicating rows in the counts
            nno_leaders=Count(
                "id", filter=~Q(Exists(leads.filter(project_id=OuterRef("pk"))))
            ),
        )

    @staticmethod
    def get_finance_stats(now: datetime) -> dict:
        """
        Counts transactions that need attention.
        """
        return Transaction.objects.aggregate(
            npending=Count("id", filter=Q(status__in=PENDING_STATUSES)),
            nfailed_week=Count(
                "id",
                filter=Q(status="Failed", created_at__gte=now - FAILED_WINDOW),
            ),
        )

    @staticmethod
    def get_alerts(
        now: datetime,
        stats: dict,
        show_finances: bool = False,
    ) -> list[dict]:
        """
        Collects issues that likely need someone to step in.

        Args:
            now: The current time, used for the stale and failed cutoffs.
            stats: The combined project and (optionally) finance counts.
            show_finances: Whether to include transaction alerts.

        Returns:
            A list of dictionaries with a `level` (bootstrap color), `icon`,
            `count`, `message`, and a `url` to the matching entries.
        """
        stale_date = (now - STALE_AFTER).date().isoformat()
        alerts = [
            dict(
                count=stats["nstaged"],
                level="danger",
                icon="bi-trash",
                message="Projects staged for deletion",
                url=explorer_url("Project", status="Staged for Deletion"),
            ),
            dict(
                count=stats["nrequires_update"],
                level="warning",
                icon="bi-exclamation-triangle",
                message="Projects that require an update from their leaders",
                url=explorer_url(
                    "Project", status="Requires Update", order_by="updated_at"
                ),
            ),
            dict(
                count=stats["nstale"],
                level="warning",
                icon="bi-hourglass-bottom",
                message="Active projects without any updates in the past year",
                url=explorer_url(
                    "Project",
                    status="Active",
                    updated_at__lt=stale_date,
                    order_by="updated_at",
                ),
            ),
            dict(
                count=stats["nno_leaders"],
                level="warning",
                icon="bi-person-x",
                message="Projects without any leaders",
                url=explorer_url("Project", leaders__isnull="true"),
            ),
            dict(
                count=stats["nreview"],
                level="info",
                icon="bi-clipboard-check",
                message="Projects waiting for review",
                url=explorer_url(
                    "Project", status="Under Review", order_by="created_at"
                ),
            ),
        ]
        if show_finances:
            alerts += [
                dict(
                    count=stats["nfailed_week"],
                    level="danger",
                    icon="bi-x-circle",
                    message="Transactions that failed in the past 7 days",
                    url=explorer_url(
                        "Transaction",
                        status="Failed",
                        created_at__gte=(now - FAILED_WINDOW).date().isoformat(),
                        order_by="-created_at",
                    ),
                ),
                dict(
                    count=stats["npending"],
                    level="secondary",
                    icon="bi-hourglass",
                    message="Transactions that are pending or under review",
                    url=explorer_url(
                        "Transaction",
                        status__in=json.dumps(PENDING_STATUSES),
                        order_by="created_at",
                    ),
                ),
            ]
        return [alert for alert in alerts if alert["count"]]

    @staticmethod
    def get_project_tree(limit: int = 12) -> list[Project]:
        """
        Grabs top-level projects (most recently updated first) along with
        their sub-projects. Each project gets `nleaders`, `nmembers`, and
        `status_theme` attributes.
        """
        base = Project.objects.annotate(
            nleaders=Count("leaders", distinct=True),
            nmembers=Count("members", distinct=True),
        ).only("name", "status", "discipline", "updated_at")
        children = base.only("parent_project_id").order_by("name")
        projects = list(
            base.filter(parent_project__isnull=True)
            .prefetch_related(
                Prefetch("child_projects", queryset=children, to_attr="children")
            )
            .order_by("-updated_at")[:limit]
        )
        for project in projects:
            for entry in [project, *project.children]:
                entry.status_theme = STATUS_THEMES.get(entry.status, "secondary")
        return projects

    @staticmethod
    def get_disciplines() -> list[dict]:
        """
        Counts projects (total and active) for each discipline.
        """
        return list(
            Project.objects.values("discipline")
            .annotate(
                total=Count("id"),
                nactive=Count("id", filter=Q(status="Active")),
            )
            .order_by("-total", "discipline")
        )

    @staticmethod
    def get_my_projects(user: User = None, limit: int = 8) -> list[Project]:
        """
        Grabs the projects that a user leads or is a member of. Each project
        gets `role` and `status_theme` attributes.
        """
        if not user or not user.is_authenticated:
            return []
        projects = list(
            Project.objects.filter(Q(leaders=user) | Q(members=user))
            .distinct()
            .annotate(
                is_leader=Exists(
                    Project.leaders.through.objects.filter(
                        project_id=OuterRef("pk"), user_id=user.id
                    )
                )
            )
            .select_related("parent_project")
            .only("name", "status", "updated_at", "parent_project__name")
            .order_by("-updated_at")[:limit]
        )
        for project in projects:
            project.role = "Leader" if project.is_leader else "Member"
            project.status_theme = STATUS_THEMES.get(project.status, "secondary")
        return projects

    @staticmethod
    def get_recent_transactions(limit: int = 8) -> list[Transaction]:
        """
        Grabs the most recent transactions, along with the wallets involved.
        Each transaction gets a `status_theme` attribute.
        """
        transactions = list(
            Transaction.objects.select_related(
                "from_wallet__project",
                "from_wallet__user",
                "to_wallet__project",
                "to_wallet__user",
            ).order_by("-created_at")[:limit]
        )
        for transaction in transactions:
            transaction.status_theme = TRANSACTION_STATUS_THEMES.get(
                transaction.status, "secondary"
            )
            transaction.from_label = wallet_label(transaction.from_wallet)
            transaction.to_label = wallet_label(transaction.to_wallet)
        return transactions


def explorer_url(table: str, **query) -> str:
    """
    Link to a data explorer table, filtered by the given query parameters.
    """
    return reverse("data_explorer:table", args=[table]) + "?" + urlencode(query)


def wallet_label(wallet: Wallet) -> str:
    """
    A short, human-readable name for a wallet (e.g. "Zeus" or "chemist1").
    """
    if wallet is None:
        return "--"
    if wallet.project:
        return wallet.project.name
    if wallet.user:
        return wallet.user.username
    return wallet.wallet_type or f"Wallet {wallet.id}"
