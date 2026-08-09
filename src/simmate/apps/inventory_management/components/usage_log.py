# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import UsageLog


class UsageLogComponent(TableComponent):
    table = UsageLog

    display_name = "Containers Usage Logs"
    description_short = (
        "Instances where a user interacts with a container, such as removing "
        "some material for an experiment."
    )

    template_names = {
        "entries": "inventory_management/usage_log/table.html",
        "entry": "inventory_management/usage_log/view.html",
        "search": "inventory_management/usage_log/form.html",
        "create": "inventory_management/usage_log/form.html",
        "update": "inventory_management/usage_log/form.html",
    }

    enabled_component_types = [
        "dashboard",
        "entries",
        "entry",
        "search",
        "create",
        "update",
    ]

    tabtitle_label_col = "id"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "container_id",
        "amount_removed",
    ]

    def mount_for_create(self):
        # Auto-fill user if we have access to request
        if hasattr(self, "request") and self.request and self.request.user:
            self.update_form("user_id", self.request.user.id)

    # -------------------------------------------------------------------------

    # UPDATE

    mount_for_update_columns = [
        "container_id",
        "user_id",
        "amount_removed",
        "comments",
    ]
