# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import StorageLocation


class StorageLocationForm(DynamicTableForm):

    table = StorageLocation

    template_name = "inventory_management/storage_location/form.html"

    # -------------------------------------------------------------------------

    # CREATE

    required_inputs = [
        "name",
        "temperature_celsius",
        "description",
    ]

    def mount_for_create(self):
        self.update_form("temperature_celsius", 20)

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
