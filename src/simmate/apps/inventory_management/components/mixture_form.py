# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import Mixture


class MixtureForm(DynamicTableForm):
    table = Mixture

    display_name = "Mixtures"
    description_short = (
        "Mixtures are the combination of two or more substances. "
        "For example, a solution would be a mixture of two substances: NaCl and water. "
        "This table includes mixtures of both specified and unspecified ratios, "
        "meaning 'salt water' and '0.1M salt water' can be separate entries."
    )

    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "inventory_management/mixture/table.html",
        "entry": "inventory_management/mixture/view.html",
    }
    template_name = "inventory_management/mixture/form.html"

    enabled_forms = [
        "search",
        "create",
        "update",
    ]

    tabtitle_label_col = "id"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "mixture_type",
        "substances__ids",
    ]

    # -------------------------------------------------------------------------

    # UPDATE

    mount_for_update_columns = [
        "mixture_type",
        "description",
        "common_name",
        "synonyms",
        "substances__ids",
    ]

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: Mixture) -> dict:

        count_limit = 50_000

        substances__limit = 10
        substances__count = table_entry.substances.all()[:count_limit].count()
        substances = table_entry.substances.order_by("-id").all()[:substances__limit]
        substances__truncated = bool(len(substances) >= substances__limit)

        return {
            "substances": substances,
            "substances__count": substances__count,
            "substances__truncated": substances__truncated,
        }
