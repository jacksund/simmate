import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.core.paginator import Page, Paginator
from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import render
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

PROJECTS_PER_PAGE = 50
"""
How many projects are shown at once in the project browser.
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
    (stale projects, projects without leaders, etc.), a project browser, and
    the signed-in user's projects. Wallet and transaction panels are only
    shown when `settings.website.show_finances` is True.

    The project browser works like a file explorer, where projects with
    sub-projects act as folders. The project (and page) a viewer has open is
    kept on their instance of this component, and browsing only re-renders
    that card (see `open_project`).
    """

    template_name = "project_management/dashboard.html"

    refresh_interval = "60s"

    project_path: list[Project] = None
    """
    The projects opened in the project browser, from the top level down
    (i.e. the breadcrumb). Empty when viewing the top-level projects.
    """

    project_page: int = 1
    """
    The page of the open project's sub-projects being shown.
    """

    def mount(self):
        self.project_path = []

    @property
    def current_project_id(self) -> int | None:
        """
        The id of the project open in the project browser, or None when
        viewing the top-level projects.
        """
        return self.project_path[-1].id if self.project_path else None

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
            sub_projects=self.get_sub_projects(
                self.current_project_id, self.project_page
            ),
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
    def get_sub_projects(parent_id: int | None, page: int = 1) -> Page:
        """
        Grabs one page of the projects directly inside of a project, sorted by
        name. Each project gets `nchild_projects`, `nleaders`, `nmembers`, and
        `status_theme` attributes.

        Args:
            parent_id: The id of the project to look inside of. Use None for
                the top-level projects.
            page: The page number to grab. Out-of-range pages give the last
                page instead.
        """
        # joins would multiply rows (children x leaders x members) and these
        # only need to run for the projects on this page
        nchild_projects = (
            Project.objects.filter(parent_project=OuterRef("pk"))
            .order_by()
            .values("parent_project")
            .annotate(count=Count("id"))
            .values("count")
        )
        nleaders = (
            Project.leaders.through.objects.filter(project_id=OuterRef("pk"))
            .order_by()
            .values("project_id")
            .annotate(count=Count("id"))
            .values("count")
        )
        nmembers = (
            Project.members.through.objects.filter(project_id=OuterRef("pk"))
            .order_by()
            .values("project_id")
            .annotate(count=Count("id"))
            .values("count")
        )
        projects = (
            Project.objects.filter(parent_project_id=parent_id)
            .only("name", "status", "discipline", "updated_at")
            .annotate(
                nchild_projects=Coalesce(Subquery(nchild_projects), 0),
                nleaders=Coalesce(Subquery(nleaders), 0),
                nmembers=Coalesce(Subquery(nmembers), 0),
            )
            .order_by("name", "id")
        )
        page = Paginator(projects, PROJECTS_PER_PAGE).get_page(page)
        for project in page:
            project.status_theme = STATUS_THEMES.get(project.status, "secondary")
        return page

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

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def open_project(self, project_id: int = None, page: int = 1):
        """
        Opens a project in the project browser and re-renders only that card.

        Args:
            project_id: The project to open. This can be a sub-project of the
                open project, a project in the breadcrumb, or None for the
                top-level projects.
            page: The page of sub-projects to show.
        """
        path_ids = [project.id for project in self.project_path]
        if project_id is None:
            self.project_path = []
        elif project_id in path_ids:
            # a breadcrumb, or another page of the open project
            self.project_path = self.project_path[: path_ids.index(project_id) + 1]
        else:
            # Only sub-projects of the open project can be opened. This keeps
            # the breadcrumb valid without looking up each parent, and ignores
            # stale clicks (e.g. a double-click on a row)
            project = (
                Project.objects.filter(
                    id=project_id,
                    parent_project_id=self.current_project_id,
                )
                .only("name")
                .first()
            )
            if project:
                self.project_path.append(project)
        self.project_page = page

        return render(
            self.request,
            "project_management/dashboard_projects.html",
            {
                "component": self,
                "sub_projects": self.get_sub_projects(
                    self.current_project_id, self.project_page
                ),
            },
        )


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
