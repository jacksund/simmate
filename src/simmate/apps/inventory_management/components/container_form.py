# -*- coding: utf-8 -*-

from functools import cached_property

from simmate.website.htmx.components import DynamicTableForm

from ..models import Container, StorageLocation


class ContainerForm(DynamicTableForm):

    table = Container

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

    # UPDATE

    # -------------------------------------------------------------------------

    # CREATE MANY
    # disabled

    # -------------------------------------------------------------------------

    # UPDATE MANY
    # disabled

    # -------------------------------------------------------------------------

    # SEARCH

    # -------------------------------------------------------------------------

    @cached_property
    def location_options(self):
        # TODO: limit user/project-linked locations
        locations = (
            StorageLocation.objects.order_by("name").values_list("id", "name").all()
        )
        return [(id, name) for id, name in locations]
