# -*- coding: utf-8 -*-

import json
from collections import defaultdict
from datetime import datetime, timedelta

import cloudpickle
import pandas
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone

from simmate.compute import SimmateExecutor, SimmateWorker, WorkItem
from simmate.compute.worker import STALE_AFTER
from simmate.website.htmx.components import HtmxComponent

from .work_item import WorkItemComponent

SLOW_REFRESH = timedelta(seconds=60)
"""
How often the more expensive panels (activity timeline, workflow health
table, and catalog counts) are rebuilt. Everything else updates on every `refresh_interval`.
"""

TIMELINE_PERIODS = {
    "24h": timedelta(days=1),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

TIMELINE_VIEWS = [
    ("activity", "Status Activity"),
    ("queue_depth", "Queue Depth"),
    ("jobs", "Jobs by Worker"),
    ("durations", "Durations"),
]

TIMELINE_LIMIT = 20_000
"""
The maximum number of WorkItems loaded for the activity timeline.
"""

STATUS_FILTERS = [
    ("", "All"),
    ("R", "Running"),
    ("P", "Pending"),
    ("E", "Errored"),
]

CATALOGS = [
    # (model, title, description, icon)
    (
        WorkItem,
        "Work Items",
        "Queued, running, and finished tasks submitted to workers",
        "bi-list-task text-primary",
    ),
    (
        SimmateWorker,
        "Workers",
        "Worker processes that poll queues and run work items",
        "bi-hdd-stack text-success",
    ),
]


class ComputeDashboardComponent(HtmxComponent):
    """
    Compute dashboard showing key operational metrics, items that need
    attention (stale workers, unserved queues, etc.), per-workflow health,
    and the worker pool. Staff users can also cancel items and shut down
    workers from here.
    """

    template_name = "compute_management/dashboard.html"

    refresh_interval = "15s"

    status_filter: str = ""

    expanded_host: str = ""

    timeline_period: str = "24h"

    timeline_view: str = "activity"

    _slow_context: dict = None
    _slow_context_time: datetime = None

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_context(self):
        ctx = super().get_context()
        now = timezone.now()

        stats = SimmateExecutor.get_stats()
        stats_24h = SimmateExecutor.get_stats(since=now - timedelta(days=1))
        stats_7d = SimmateExecutor.get_stats(since=now - timedelta(days=7))

        active_workers = list(
            SimmateWorker.get_active()
            .only(
                "id",
                "status",
                "computer_system",
                "ncores",
                "ram",
                "nitems_completed",
                "shutdown_flag",
                "tags",
                "updated_at",
            )
            .order_by("computer_system", "id")
        )
        nstale = SimmateWorker.get_stale().count()
        norphaned = (
            WorkItem.objects.filter(status="R", worker__isnull=False)
            .exclude(worker__in=SimmateWorker.get_active())
            .count()
        )
        unserved_queues = self.get_unserved_queues(
            [worker.tags for worker in active_workers]
        )

        ctx.update(
            last_updated=now,
            can_manage=self.can_manage,
            status_filters=STATUS_FILTERS,
            timeline_periods=list(TIMELINE_PERIODS.keys()),
            timeline_views=TIMELINE_VIEWS,
            timeline_limit=TIMELINE_LIMIT,
            alerts=self.get_alerts(
                stats=stats,
                stats_24h=stats_24h,
                stats_7d=stats_7d,
                nstale=nstale,
                norphaned=norphaned,
                unserved_queues=unserved_queues,
            ),
            recent_work_items=self.get_recent_work_items(self.status_filter),
            worker_hosts=self.get_worker_hosts(active_workers),
            **self.get_slow_context(),
        )
        return ctx

    def get_slow_context(self) -> dict:
        """
        Builds (or reuses) the context for the more expensive panels, which
        only need to update every `SLOW_REFRESH`.
        """
        now = timezone.now()
        if self._slow_context is None or now - self._slow_context_time > SLOW_REFRESH:
            timeline_start = now - TIMELINE_PERIODS[self.timeline_period]
            timeline_df = self.get_timeline_df(timeline_start)
            report = WorkItemComponent.get_report_from_df(
                timeline_df,
                start=timeline_start,
                end=now,
                views=[self.timeline_view],
            )
            self._slow_context = dict(
                timeline_figure=report.get(self.timeline_view),
                timeline_count=len(timeline_df),
                workflow_health=self.get_workflow_health(),
                catalogs=[
                    dict(
                        table=model.__name__,
                        title=title,
                        description=description,
                        icon=icon,
                        count=f"{model.objects.count():,}",
                    )
                    for model, title, description, icon in CATALOGS
                ],
            )
            self._slow_context_time = now
        return self._slow_context

    def clear_slow_context(self):
        self._slow_context = None

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    @staticmethod
    def get_unserved_queues(worker_tags: list[list[str]], limit: int = 5) -> list[dict]:
        """
        Finds pending WorkItems that no active worker will pick up. A worker
        runs an item when all of the worker's tags are present on the item
        (see `SimmateWorker.start`).

        Args:
            worker_tags: The tags of every active worker.
            limit: The maximum number of tag groups to return.

        Returns:
            A list of dictionaries, one per unique set of tags, sorted by the
            number of pending items.
        """
        pending_groups = (
            WorkItem.objects.filter(status="P")
            .values("tags")
            .annotate(n=Count("id"))
            .order_by("-n")
        )

        unserved = []
        for group in pending_groups:
            tags = group["tags"] or []
            is_served = any(
                set(wtags).issubset(tags) if wtags else not tags
                for wtags in worker_tags
            )
            if not is_served:
                unserved.append(
                    {
                        "tags": tags,
                        "tags_json": json.dumps(tags),
                        "count": group["n"],
                    }
                )
        return unserved[:limit]

    @staticmethod
    def get_alerts(
        stats: dict,
        stats_24h: dict,
        stats_7d: dict,
        nstale: int,
        norphaned: int,
        unserved_queues: list[dict],
    ) -> list[dict]:
        """
        Collects issues that likely need someone to step in.

        Returns:
            A list of dictionaries with a `level` (bootstrap color), `icon`,
            `message`, and an optional `action` that the template renders
            as a button.
        """
        alerts = []

        if nstale:
            alerts.append(
                {
                    "level": "danger",
                    "icon": "bi-heartbreak",
                    "message": (
                        f"{nstale} worker{'s' if nstale != 1 else ''} "
                        f"haven't checked in for over "
                        f"{int(STALE_AFTER.total_seconds() // 60)} minutes "
                        "and were likely killed."
                    ),
                    "action": {"method": "mark_stale", "label": "Mark stale"},
                }
            )

        if norphaned:
            alerts.append(
                {
                    "level": "danger",
                    "icon": "bi-exclamation-octagon",
                    "message": (
                        f"{norphaned} work item{'s are' if norphaned != 1 else ' is'} "
                        "still marked running on a worker that is no longer "
                        "active. These will never finish on their own."
                    ),
                }
            )

        for queue in unserved_queues:
            tags = ", ".join(queue["tags"]) or "(no tags)"
            alerts.append(
                {
                    "level": "warning",
                    "icon": "bi-inbox",
                    "message": (
                        f"{queue['count']:,} pending item"
                        f"{'s' if queue['count'] != 1 else ''} tagged "
                        f"[{tags}] have no active worker able to run them."
                    ),
                    "action": {
                        "method": "cancel_unserved",
                        "label": "Cancel all",
                        "kwarg": "tags",
                        "value": queue["tags_json"],
                        "confirm": f"Cancel {queue['count']} pending items tagged [{tags}]?",
                    },
                }
            )

        if stats["nrunning_long"]:
            alerts.append(
                {
                    "level": "warning",
                    "icon": "bi-clock-history",
                    "message": (
                        f"{stats['nrunning_long']} work item"
                        f"{'s have' if stats['nrunning_long'] != 1 else ' has'} "
                        "been running for more than 24 hours."
                    ),
                }
            )

        # only flag an error spike when there is enough data to be meaningful
        ndone_24h = stats_24h["nfinished"] + stats_24h["nerrored"]
        rate_24h = stats_24h["error_percent"]
        rate_7d = stats_7d["error_percent"]
        if ndone_24h >= 10 and rate_24h > max(2 * rate_7d, rate_7d + 10):
            alerts.append(
                {
                    "level": "warning",
                    "icon": "bi-graph-up-arrow",
                    "message": (
                        f"Error rate over the last 24h is {rate_24h:.0f}%, "
                        f"up from {rate_7d:.0f}% over the last 7 days."
                    ),
                }
            )

        return alerts

    @staticmethod
    def get_timeline_df(start: datetime) -> pandas.DataFrame:
        """
        Loads every WorkItem that was active at some point after `start`: all
        pending/running items plus anything finished or cancelled since.

        Args:
            start: The beginning of the timeline window.

        Returns:
            A dataframe with the columns needed by `WorkItemComponent` reports.
        """
        return (
            WorkItem.objects.filter(Q(updated_at__gte=start) | Q(status__in=["P", "R"]))
            .order_by("-updated_at")
            .to_dataframe(WorkItemComponent.report_df_columns, limit=TIMELINE_LIMIT)
        )

    @classmethod
    def get_workflow_health(cls, days: int = 7) -> list[dict]:
        """
        Summarizes the state of each workflow: everything currently queued or
        running, plus what finished or failed within the last `days`.

        Args:
            days: How far back to count finished and failed WorkItems.

        Returns:
            A list of dictionaries, one per workflow, with the most failures
            listed first.
        """
        groups = (
            WorkItem.objects.filter(
                Q(status__in=["P", "R"])
                | Q(
                    status__in=["F", "E"],
                    updated_at__gte=timezone.now() - timedelta(days=days),
                )
            )
            .values("tags", "status")
            .annotate(n=Count("id"))
            .order_by()
        )

        counts = defaultdict(lambda: {"P": 0, "R": 0, "F": 0, "E": 0})
        for group in groups:
            name = WorkItem.get_workflow_name(group["tags"])
            counts[name][group["status"]] += group["n"]

        health = []
        for name, c in counts.items():
            ndone = c["F"] + c["E"]
            health.append(
                {
                    "name": name,
                    "npending": c["P"],
                    "nrunning": c["R"],
                    "nfinished": c["F"],
                    "nerrored": c["E"],
                    "error_percent": round(c["E"] / ndone * 100) if ndone else None,
                }
            )
        health.sort(key=lambda row: (-row["nerrored"], -row["npending"], row["name"]))
        return health

    @classmethod
    def get_recent_work_items(
        cls,
        status: str = "",
        limit: int = 10,
    ) -> list[WorkItem]:
        """
        Grabs the most recently updated WorkItems for the live table. Errored
        items also get an `error_message` attribute.

        Args:
            status: Optionally only include WorkItems with this status.
            limit: The maximum number of WorkItems to return.

        Returns:
            A list of WorkItems.
        """
        # BUG: `only` is required to avoid loading the pickled binary columns
        work_items = WorkItem.objects.select_related("worker").only(
            "id",
            "status",
            "tags",
            "created_at",
            "updated_at",
            "worker__computer_system",
        )
        if status:
            work_items = work_items.filter(status=status)
        work_items = list(work_items.order_by("-updated_at")[:limit])

        errors = cls.get_error_messages(
            [item.id for item in work_items if item.status == "E"]
        )

        for item in work_items:
            item.error_message = errors.get(item.id)
        return work_items

    @staticmethod
    def get_error_messages(ids: list, max_length: int = 150) -> dict:
        """
        Unpickles the results of errored WorkItems into short error messages.

        Args:
            ids: The ids of errored WorkItems.
            max_length: Messages are truncated to this many characters.

        Returns:
            A dictionary mapping WorkItem id to its error message.
        """
        if not ids:
            return {}

        errors = {}
        results = WorkItem.objects.filter(id__in=ids).values_list("id", "result_binary")
        for item_id, result_binary in results:
            try:
                error = cloudpickle.loads(result_binary)
                message = f"{type(error).__name__}: {error}"
            except Exception:
                message = "(error could not be loaded)"
            if len(message) > max_length:
                message = message[: max_length - 1] + "…"
            errors[item_id] = message
        return errors

    @staticmethod
    def get_worker_hosts(active_workers: list[SimmateWorker]) -> list[dict]:
        """
        Groups active workers by the computer system they are running on.

        Args:
            active_workers: Workers that are active and have a fresh heartbeat.

        Returns:
            A list of dictionaries, one per host, sorted by number of workers.
        """
        workers_by_host = defaultdict(list)
        for worker in active_workers:
            workers_by_host[worker.computer_system or "Unknown host"].append(worker)

        worker_hosts = []
        for name, workers in workers_by_host.items():
            nworkers = len(workers)
            nrunning = sum(w.status == "Running" for w in workers)
            utilization = round(nrunning / nworkers * 100)
            if utilization >= 85:
                badge = (
                    "Busy",
                    "bi-lightning-charge",
                    "warning",
                )
            elif nrunning:
                badge = ("Healthy", "bi-check-circle", "success")
            else:
                badge = (
                    "Idle",
                    "bi-pause-circle",
                    "secondary",
                )

            worker_hosts.append(
                {
                    "name": name,
                    "workers": workers,
                    "nworkers": nworkers,
                    "nrunning": nrunning,
                    "ncores": sum(w.ncores or 0 for w in workers),
                    "ram": sum(w.ram or 0 for w in workers),
                    "nitems": sum(w.nitems_completed or 0 for w in workers),
                    "last_heartbeat": max(w.updated_at for w in workers),
                    "utilization": utilization,
                    "badge_text": badge[0],
                    "badge_icon": badge[1],
                    "badge_theme": badge[2],
                }
            )
        worker_hosts.sort(key=lambda host: -host["nworkers"])
        return worker_hosts

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    @property
    def can_manage(self) -> bool:
        user = getattr(self.request, "user", None)
        return bool(user and user.is_staff)

    def _check_can_manage(self) -> bool:
        if not self.can_manage:
            self.action_error = "Only staff users can manage compute resources."
            return False
        return True

    def set_status_filter(self, status: str = ""):
        valid = [key for key, _ in STATUS_FILTERS]
        self.status_filter = status if status in valid else ""

    def set_timeline_period(self, period: str = ""):
        if period in TIMELINE_PERIODS:
            self.timeline_period = period
            self.clear_slow_context()

    def set_timeline_view(self, view: str = ""):
        if view in dict(TIMELINE_VIEWS):
            self.timeline_view = view
            self.clear_slow_context()

    def toggle_host(self, host: str = ""):
        host = str(host)
        self.expanded_host = "" if host == self.expanded_host else host

    def cancel_item(self, item: str = ""):
        if not self._check_can_manage():
            return
        try:
            work_item = WorkItem.objects.only("id", "status").get(id=item)
        except (WorkItem.DoesNotExist, ValidationError):
            self.action_error = f"Unknown work item: {item}"
            return
        if work_item.cancel():
            self.action_message = f"Canceled work item {str(work_item.id)[:8]}"
        else:
            self.action_error = (
                f"Work item {str(work_item.id)[:8]} is no longer pending "
                "and cannot be canceled."
            )

    def cancel_unserved(self, tags: list = None):
        if not self._check_can_manage():
            return
        if not isinstance(tags, list):
            self.action_error = f"Invalid tags: {tags}"
            return
        ncanceled = WorkItem.objects.filter(status="P", tags=tags).update(status="C")
        self.action_message = f"Canceled {ncanceled:,} pending work items"

    def shutdown_worker(self, worker: int = None):
        if not self._check_can_manage():
            return
        if not isinstance(worker, int):
            self.action_error = f"Unknown worker: {worker}"
            return
        nupdated = SimmateWorker.objects.filter(id=worker).update(shutdown_flag=True)
        if nupdated:
            self.action_message = (
                f"Worker {worker} will shut down after its current work item"
            )
        else:
            self.action_error = f"Unknown worker: {worker}"

    def mark_stale(self):
        if not self._check_can_manage():
            return
        nmarked = SimmateWorker.mark_stale_workers()
        self.action_message = f"Marked {nmarked} worker(s) as stale"
