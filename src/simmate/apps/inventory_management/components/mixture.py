from django.db.models import F

from simmate.website.data_explorer.components import TableComponent

from ..models import Container, Mixture, UsageLog


class MixtureComponent(TableComponent):
    table = Mixture

    display_name = "Mixtures"
    description_short = (
        "Mixtures are the combination of two or more substances. "
        "For example, a solution would be a mixture of two substances: NaCl and water. "
        "This table includes mixtures of both specified and unspecified ratios, "
        "meaning 'salt water' and '0.1M salt water' can be separate entries."
    )

    template_names = {
        "entries": "inventory_management/mixture/table.html",
        "entry": "inventory_management/mixture/view.html",
        "search": "inventory_management/mixture/form.html",
        "create": "inventory_management/mixture/form.html",
        "update": "inventory_management/mixture/form.html",
    }

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "search",
        "create",
        "update",
    ]

    tabtitle_label_col = "display_id"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "mixture_type",
        "substances__ids",
    ]

    def check_form_for_create(self):
        super().check_form_for_create()
        if not self.form_data.get("id_prefix"):
            self.form_data["id_prefix"] = Mixture.generate_id_prefix()

    # -------------------------------------------------------------------------

    # UPDATE

    mount_for_update_columns = [
        "mixture_type",
        "description",
        "common_name",
        "synonyms",
        "substances__ids",
    ]

    # -------------------------------------------------------------------------

    # ENTRY VIEW

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: Mixture) -> dict:
        limit = 25
        # in-stock batches and containers first (`is_depleted` is nullable)
        in_stock_first = (F("is_depleted").asc(nulls_first=True), "-id")

        # the substances in the mixture, along with their role and amount
        components = table_entry.components.select_related(
            "substance__molecule"
        ).order_by("id")
        components__count = components.count()
        components = list(components[:limit])

        # physical inventory of the mixture
        batches = table_entry.batches.all()
        batches__count = batches.count()
        containers = Container.get_web_queryset().filter(batch__mixture=table_entry)
        containers__count = containers.count()
        usage_logs = UsageLog.objects.filter(
            source_container__batch__mixture=table_entry
        ).select_related("source_container", "user")
        usage_logs__count = usage_logs.count()

        return {
            "mixture_components": components,
            "mixture_components__count": components__count,
            "mixture_components__truncated": components__count > limit,
            "batches": batches.order_by(*in_stock_first)[:limit],
            "batches__count": batches__count,
            "batches__truncated": batches__count > limit,
            "containers": containers.order_by(*in_stock_first)[:limit],
            "containers__count": containers__count,
            "containers__truncated": containers__count > limit,
            "usage_logs": usage_logs.order_by("-created_at", "-id")[:limit],
            "usage_logs__count": usage_logs__count,
            "usage_logs__truncated": usage_logs__count > limit,
        }
