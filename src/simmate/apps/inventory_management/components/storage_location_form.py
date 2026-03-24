# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import StorageLocation


class StorageLocationForm(DynamicTableForm):

    table = StorageLocation

    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "inventory_management/storage_location/table.html",
        "entry": "inventory_management/storage_location/view.html",
    }

    html_display_name = "Storage Locations"
    html_description_short = (
        "Specific areas where chemical containers are stored. Locations can be "
        "anything from an entire building to a specific cabinet. Locations "
        "can also have 'parent locations' to allow folder-like organization."
    )

    html_form_component = "storage-location-form"
    html_enabled_forms = [
        "search",
        "create",
        "update",
    ]

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
