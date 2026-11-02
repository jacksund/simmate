from django.db.models import Count

from simmate.compute import SimmateWorker
from simmate.website.data_explorer.components import TableComponent


class SimmateWorkerComponent(TableComponent):
    table = SimmateWorker
    display_name = "Workers"
    description_short = (
        "Computational agents responsible for executing submitted tasks. "
        "This table monitors the health, resource usage, and active jobs "
        "for each worker in the cluster."
    )
    template_names = {
        "entries": "compute_management/workers/table.html",
        "entry": "compute_management/workers/view.html",
    }

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: SimmateWorker) -> dict:

        work_items__limit = 20
        # BUG: `only` is required to avoid loading the pickled binary columns
        work_items = (
            table_entry.work_items.select_related("worker")
            .only(
                "id",
                "name",
                "status",
                "created_at",
                "started_at",
                "updated_at",
                "worker__computer_system",
            )
            .order_by("-updated_at")[:work_items__limit]
        )

        work_item_counts = dict(
            table_entry.work_items.values_list("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return {
            "work_items": work_items,
            "work_items__limit": work_items__limit,
            "work_items__count": sum(work_item_counts.values()),
            "work_item_counts": work_item_counts,
        }
