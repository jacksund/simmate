# -*- coding: utf-8 -*-

from functools import cached_property

from simmate.website.htmx.components import DynamicTableForm

from ..models import Container, StorageLocation


class ContainerForm(DynamicTableForm):

    table = Container

    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "inventory_management/container/table.html",
        "entry": "inventory_management/container/view.html",
    }

    display_name = "Containers"
    description_short = (
        "Containers are specific vessels that contain part (or all) of a batch. A "
        "single batch can have multiple containers because batches might need to be "
        "split up and/or have different storage destinations."
    )

    enabled_forms = [
        "search",
        "create",
        "update",
    ]

    template_name = "inventory_management/container/form.html"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "batch_id",
        "location_id",
        # "barcode",
        "initial_amount",
        "amount_units",
    ]

    def mount_for_create(self):
        self.update_form("amount_units", "mg")
        self.update_form("is_depleted", False)

    def unmount_for_create(self):
        self.update_form("current_amount", self.form_data["initial_amount"])

    # -------------------------------------------------------------------------

    @cached_property
    def location_options(self):
        # TODO: limit user/project-linked locations
        locations = (
            StorageLocation.objects.order_by("name").values_list("id", "name").all()
        )
        return [(id, name) for id, name in locations]
