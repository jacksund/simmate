# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Count, F, Q
from django.urls import reverse
from django.utils import timezone

from simmate.website.htmx.components import HtmxComponent

from ..models import (
    Batch,
    Container,
    Mixture,
    StorageLocation,
    Substance,
    UsageLog,
)

SLOW_REFRESH = timedelta(minutes=5)
"""
How often the stock-level panels (which scan the batch and container tables)
are rebuilt. Usage activity updates on every `refresh_interval`.
"""

EXPIRING_WITHIN = timedelta(days=30)
"""
Batches that expire within this window are flagged as "expiring soon".
"""

LOW_STOCK_FRACTION = Decimal("0.10")
"""
Containers with less than this fraction of their `initial_amount` remaining
are flagged as low stock.
"""

COLD_STORAGE_MAX = 4
"""
Locations at or below this temperature (in Celsius) are labeled cold storage.
"""

IN_STOCK = ~Q(is_depleted=True)
"""
Batches and containers that still have material (`is_depleted` is nullable,
so unset entries count as in stock).
"""

CATALOGS = [
    # (table, title, description, icon)
    (
        "Substance",
        "Substances",
        "Registered chemical identities and their IDs",
        "bi-hexagon text-primary",
    ),
    (
        "Mixture",
        "Mixtures",
        "Solutions, blends, and other formulations",
        "bi-bezier2 text-danger",
    ),
    (
        "Batch",
        "Batches",
        "Synthesized products and purchased lots",
        "bi-layers text-warning",
    ),
    (
        "Container",
        "Containers",
        "Vials, bottles, and other vessels holding a batch",
        "bi-box-seam text-info",
    ),
    (
        "StorageLocation",
        "Storage Locations",
        "Rooms, cabinets, freezers, and gloveboxes",
        "bi-geo-alt text-success",
    ),
    (
        "UsageLog",
        "Usage Logs",
        "Records of material removed from containers",
        "bi-clock-history text-secondary",
    ),
]


class InventoryDashboardComponent(HtmxComponent):
    """
    Inventory dashboard showing stock levels, items that need attention
    (expired batches, low-stock containers, etc.), recent usage, and where
    containers are stored.

    NOTE: The `Substance` table can grow to trillions of rows, so it is never
    counted, filtered, or aggregated here. Substances are only loaded through
    joins from the (much smaller) batch, container, and usage log tables.
    """

    template_name = "inventory_management/dashboard.html"

    refresh_interval = "60s"

    # Shared by all instances (i.e. all viewers), as nothing in it depends on
    # the component's state. Set on the class in `get_slow_context`.
    _slow_stats: dict = None
    _slow_context: dict = None
    _slow_context_time: datetime = None

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_context(self):
        ctx = super().get_context()
        now = timezone.now()

        stats, slow_context = self.get_slow_context(now)

        ctx.update(
            last_updated=now,
            alerts=self.get_alerts(now, stats),
            recent_usage=self.get_recent_usage(),
            expiring_days=EXPIRING_WITHIN.days,
            **slow_context,
        )
        return ctx

    @classmethod
    def get_slow_context(cls, now: datetime) -> tuple[dict, dict]:
        """
        Builds (or reuses) the stats and context for the panels that scan the
        batch and container tables, which only need to update every
        `SLOW_REFRESH`.
        """
        if cls._slow_context is None or now - cls._slow_context_time > SLOW_REFRESH:
            stats = {
                "nsubstances": Substance.get_estimated_count(),
                **cls.get_batch_stats(now),
                **cls.get_container_stats(),
            }
            counts = {
                "Substance": f"~{format_compact(stats['nsubstances'])}",
                "Mixture": f"{Mixture.objects.count():,}",
                "Batch": f"{stats['nbatches']:,}",
                "Container": f"{stats['ncontainers']:,}",
                "StorageLocation": f"{StorageLocation.objects.count():,}",
                # append-only, so avoid an ever-slower COUNT(*)
                "UsageLog": f"~{format_compact(UsageLog.get_estimated_count())}",
            }
            cls._slow_stats = stats
            cls._slow_context = dict(
                storage_locations=cls.get_storage_locations(),
                expiring_batches=cls.get_expiring_batches(now),
                catalogs=[
                    dict(
                        table=table,
                        title=title,
                        description=description,
                        icon=icon,
                        count=counts[table],
                    )
                    for table, title, description, icon in CATALOGS
                ],
            )
            cls._slow_context_time = now
        return cls._slow_stats, cls._slow_context

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    @staticmethod
    def get_batch_stats(now: datetime) -> dict:
        """
        Counts batches by their stock and expiration status.
        """
        stats = Batch.objects.aggregate(
            nbatches=Count("id"),
            nexpired=Count("id", filter=IN_STOCK & Q(expiration_date__lt=now)),
            nexpiring=Count(
                "id",
                filter=IN_STOCK
                & Q(
                    expiration_date__gte=now, expiration_date__lt=now + EXPIRING_WITHIN
                ),
            ),
        )
        # batches with stock but no containers to hold it. This is a separate
        # query because the join would duplicate rows in the counts above
        stats["nunstored"] = Batch.objects.filter(
            IN_STOCK, containers__isnull=True
        ).count()
        return stats

    @staticmethod
    def get_container_stats() -> dict:
        """
        Counts containers by their stock and location status.
        """
        return Container.objects.aggregate(
            ncontainers=Count("id"),
            nlow=Count(
                "id",
                filter=IN_STOCK
                & Q(current_amount__gt=0)
                & Q(current_amount__lt=F("initial_amount") * LOW_STOCK_FRACTION),
            ),
            # empty containers that were never marked as depleted
            nempty=Count("id", filter=IN_STOCK & Q(current_amount__lte=0)),
            nunlocated=Count("id", filter=IN_STOCK & Q(location__isnull=True)),
        )

    @staticmethod
    def get_alerts(now: datetime, stats: dict) -> list[dict]:
        """
        Collects issues that likely need someone to step in.

        Args:
            stats: The combined batch and container counts.

        Returns:
            A list of dictionaries with a `level` (bootstrap color), `icon`,
            `count`, `message`, and a `url` to the matching entries.
        """
        today = now.date().isoformat()
        soon = (now + EXPIRING_WITHIN).date().isoformat()
        low_percent = f"{LOW_STOCK_FRACTION * 100:.0f}%"
        alerts = [
            dict(
                count=stats["nexpired"],
                level="danger",
                icon="bi-calendar-x",
                message="Batches past their expiration date that are still in stock",
                table="Batch",
                query=f"?is_depleted=false&expiration_date__lt={today}"
                "&order_by=expiration_date",
            ),
            dict(
                count=stats["nempty"],
                level="warning",
                icon="bi-exclamation-triangle",
                message="Containers with nothing left that aren't marked as depleted",
                table="Container",
                query="?is_depleted=false&current_amount__lte=0",
            ),
            dict(
                count=stats["nexpiring"],
                level="warning",
                icon="bi-calendar-event",
                message=f"Batches expiring within the next {EXPIRING_WITHIN.days} days",
                table="Batch",
                query=f"?is_depleted=false&expiration_date__gte={today}"
                f"&expiration_date__lt={soon}&order_by=expiration_date",
            ),
            dict(
                count=stats["nlow"],
                level="warning",
                icon="bi-battery-low",
                message=f"Containers with less than {low_percent} of their initial amount left",
                table="Container",
                query="?is_depleted=false&current_amount__gt=0&order_by=current_amount",
            ),
            dict(
                count=stats["nunlocated"],
                level="secondary",
                icon="bi-geo",
                message="Containers in stock without a storage location",
                table="Container",
                query="?is_depleted=false&location__isnull=true",
            ),
            dict(
                count=stats["nunstored"],
                level="secondary",
                icon="bi-inbox",
                message="Batches in stock without any containers",
                table="Batch",
                query="?is_depleted=false&containers__isnull=true",
            ),
        ]
        alerts = [alert for alert in alerts if alert["count"]]
        for alert in alerts:
            table, query = alert.pop("table"), alert.pop("query")
            alert["url"] = reverse("data_explorer:table", args=[table]) + query
        return alerts

    @staticmethod
    def get_recent_usage(limit: int = 10) -> list[UsageLog]:
        """
        Grabs the most recent usage logs, along with what was used and where
        it came from.
        """
        return list(
            UsageLog.objects.select_related(
                "user",
                "source_container__location",
                "source_container__batch__substance",
                "source_container__batch__mixture",
            )
            .only(
                "amount_removed",
                "created_at",
                "user__username",
                "source_container__amount_units",
                "source_container__location__name",
                "source_container__batch__substance__common_name",
                "source_container__batch__mixture__id_prefix",
                "source_container__batch__mixture__common_name",
            )
            .order_by("-created_at")[:limit]
        )

    @staticmethod
    def get_expiring_batches(now: datetime, limit: int = 8) -> list[Batch]:
        """
        Grabs in-stock batches that are expired or expire soon, soonest first.
        Each batch also gets `status_text` and `badge_theme` attributes.
        """
        batches = list(
            Batch.objects.filter(IN_STOCK, expiration_date__lt=now + EXPIRING_WITHIN)
            .select_related("substance", "mixture")
            .only(
                "batch_number",
                "total_current_amount",
                "amount_units",
                "supplier",
                "expiration_date",
                "substance__common_name",
                "mixture__id_prefix",
                "mixture__common_name",
            )
            .order_by("expiration_date")[:limit]
        )
        for batch in batches:
            days = (batch.expiration_date - now).days
            if days < 0:
                batch.status_text, batch.badge_theme = "expired", "danger"
            else:
                batch.status_text = f"in {days} day{'s' if days != 1 else ''}"
                batch.badge_theme = "warning"
        return batches

    @staticmethod
    def get_storage_locations(limit: int = 8) -> list[StorageLocation]:
        """
        Grabs the storage locations holding the most in-stock containers. Each
        location gets `ncontainers` and `is_cold` attributes.
        """
        # IN_STOCK, but through the reverse relation
        in_stock = Q(containers__is_depleted=False) | Q(
            containers__is_depleted__isnull=True
        )
        locations = list(
            StorageLocation.objects.annotate(
                ncontainers=Count("containers", filter=in_stock)
            )
            .filter(ncontainers__gt=0)
            .select_related("parent_location")
            .only(
                "name",
                "storage_type",
                "temperature_celsius",
                "parent_location__name",
            )
            .order_by("-ncontainers")[:limit]
        )
        for location in locations:
            location.is_cold = (
                location.temperature_celsius is not None
                and location.temperature_celsius <= COLD_STORAGE_MAX
            )
        return locations


def format_compact(value: int) -> str:
    """
    Formats large numbers compactly (e.g. 1,280 -> "1,280" and
    3_400_000_000 -> "3.4B"). Values under a million are written in full.
    """
    for threshold, suffix in [(10**12, "T"), (10**9, "B"), (10**6, "M")]:
        if value >= threshold:
            return f"{value / threshold:.1f}".rstrip("0").rstrip(".") + suffix
    return f"{value:,}"
