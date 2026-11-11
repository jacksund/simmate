from django.db.models import F
from django.utils import timezone

from simmate.website.data_explorer.components import TableComponent

from ..models import Batch, Container, UsageLog
from .substance import SubstanceComponent


class BatchComponent(TableComponent):
    table = Batch

    template_names = {
        "entries": "inventory_management/batch/table.html",
        "entry": "inventory_management/batch/view.html",
        "search": "inventory_management/batch/form.html",
        "create": "inventory_management/batch/form.html",
        "update": "inventory_management/batch/form.html",
    }

    display_name = "Batches"
    description_short = (
        "Batches are specific instances of a substance or mixture. For example, "
        "the product of a single synthesis or the delievery a purchased chemical "
        "would each be one batch. One batch can then be stored in one or more containers."
    )

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "create",
        "update",
    ]

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "is_mixture",
        # "substance_id", # only if is_mixture=False
        # "mixture_id",  # only if is_mixture=True
        # "batch_number",  # auto generated after creation (to avoid race condition)
    ]

    def mount_for_create(self):
        self.update_form("amount_units", "mg")
        self.update_form("is_depleted", False)

    def check_form_for_create(self):
        self.check_required_inputs()

        is_mixture = self.form_data["is_mixture"]
        if is_mixture and not self.form_data.get("mixture_id", None):
            self.form_errors.append(
                "'mixture_id' is a required input when `is_mixture=True"
            )
        if not is_mixture and not self.form_data.get("substance_id", None):
            self.form_errors.append(
                "'substance_id' is a required input when `is_mixture=False"
            )

    # -------------------------------------------------------------------------

    # ENTRY VIEW

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: Batch) -> dict:
        limit = 25
        # in-stock containers first (`is_depleted` is nullable)
        in_stock_first = (F("is_depleted").asc(nulls_first=True), "-id")

        containers = Container.get_web_queryset().filter(batch=table_entry)
        containers__count = containers.count()
        usage_logs = UsageLog.objects.filter(
            source_container__batch=table_entry
        ).select_related("source_container", "user")
        usage_logs__count = usage_logs.count()

        # lineage: the batches this one was made from (and those made from
        # it), plus the material that was taken from containers to make it
        parent_batches = table_entry.parent_batches.select_related(
            "substance", "mixture"
        )
        parent_batches__count = parent_batches.count()
        child_batches = table_entry.child_batches.select_related("substance", "mixture")
        child_batches__count = child_batches.count()
        source_usage_logs = table_entry.source_usage_logs.select_related(
            "source_container", "user"
        )
        source_usage_logs__count = source_usage_logs.count()

        return {
            **cls.get_item_context(table_entry),
            "is_expired": bool(
                table_entry.expiration_date
                and table_entry.expiration_date < timezone.now()
            ),
            "containers": containers.order_by(*in_stock_first)[:limit],
            "containers__count": containers__count,
            "containers__truncated": containers__count > limit,
            "usage_logs": usage_logs.order_by("-created_at", "-id")[:limit],
            "usage_logs__count": usage_logs__count,
            "usage_logs__truncated": usage_logs__count > limit,
            "parent_batches": parent_batches.order_by("-id")[:limit],
            "parent_batches__count": parent_batches__count,
            "parent_batches__truncated": parent_batches__count > limit,
            "child_batches": child_batches.order_by("-id")[:limit],
            "child_batches__count": child_batches__count,
            "child_batches__truncated": child_batches__count > limit,
            "source_usage_logs": source_usage_logs.order_by("-created_at", "-id")[
                :limit
            ],
            "source_usage_logs__count": source_usage_logs__count,
            "source_usage_logs__truncated": source_usage_logs__count > limit,
            "lineage__count": (
                parent_batches__count + child_batches__count + source_usage_logs__count
            ),
        }

    @staticmethod
    def get_item_context(batch: Batch | None) -> dict:
        """
        Gives what `for_view/item_viewer.html` needs to draw the substance or
        mixture of a batch (e.g. on the page of a batch or one of its
        containers).
        """
        mixture_components = []
        if batch and batch.mixture_id:
            mixture_components = list(
                batch.mixture.components.select_related("substance__molecule").order_by(
                    "id"
                )[:8]
            )
        return {
            "viewer_default": SubstanceComponent.get_viewer_default(
                batch.substance if batch else None
            ),
            "mixture_components": mixture_components,
        }

    # -------------------------------------------------------------------------
