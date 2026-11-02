from django.db.models import F

from simmate.website.data_explorer.components import TableComponent

from ..models import Container, StorageLocation


class StorageLocationComponent(TableComponent):
    table = StorageLocation

    template_names = {
        "entries": "inventory_management/storage_location/table.html",
        "entry": "inventory_management/storage_location/view.html",
        "search": "inventory_management/storage_location/form.html",
        "create": "inventory_management/storage_location/form.html",
        "update": "inventory_management/storage_location/form.html",
    }

    display_name = "Storage Locations"
    description_short = (
        "Specific areas where chemical containers are stored. Locations can be "
        "anything from an entire building to a specific cabinet. Locations "
        "can also have 'parent locations' to allow folder-like organization."
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
        "name",
        "temperature_celsius",
        "description",
    ]

    def mount_for_create(self):
        self.update_form("temperature_celsius", 20)

    # -------------------------------------------------------------------------

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: StorageLocation) -> dict:

        containers__limit = 25
        containers__count = table_entry.containers.count()
        containers = (
            Container.get_web_queryset()
            .filter(location=table_entry)
            # in-stock containers first (`is_depleted` is nullable)
            .order_by(F("is_depleted").asc(nulls_first=True), "-id")[:containers__limit]
        )

        return {
            "containers": containers,
            "containers__count": containers__count,
            "containers__truncated": containers__count > containers__limit,
        }
