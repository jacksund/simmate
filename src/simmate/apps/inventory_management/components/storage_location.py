from django.db.models import Count, F, Q

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

    # ENTRY VIEW

    @classmethod
    def get_extra_entry_context(cls, request, table_entry: StorageLocation) -> dict:
        limit = 25
        max_depth = 10
        max_nodes = 100

        # Walk down through the sub-locations one level at a time, which gives
        # both the tree of sub-locations and the ids of every location nested
        # in this one (for listing their containers). Only the first
        # `max_nodes` sub-locations are put in the tree.
        table_entry.tree_children = []
        nodes = {table_entry.id: table_entry}
        descendant_ids = []
        level = [table_entry.id]
        for _ in range(max_depth):
            children = (
                StorageLocation.objects.filter(parent_location_id__in=level)
                .exclude(id__in=list(nodes) + descendant_ids)  # guards cycles
                .annotate(
                    # in-stock containers (`is_depleted` is nullable)
                    ncontainers=Count(
                        "containers",
                        filter=Q(containers__is_depleted=False)
                        | Q(containers__is_depleted__isnull=True),
                    )
                )
                .order_by("name", "id")
            )
            level = []
            for child in children:
                descendant_ids.append(child.id)
                level.append(child.id)
                # the parent may have been left out of the tree by the cap
                if len(nodes) <= max_nodes and child.parent_location_id in nodes:
                    child.tree_children = []
                    nodes[child.parent_location_id].tree_children.append(child)
                    nodes[child.id] = child
            if not level:
                break
        # count all sub-locations, so that we can say how many are not shown
        counts = dict(
            StorageLocation.objects.filter(parent_location_id__in=list(nodes))
            .values_list("parent_location_id")
            .annotate(count=Count("id"))
            .order_by()
        )
        for node in nodes.values():
            node.tree_more = counts.get(node.id, 0) - len(node.tree_children)

        # containers in this location or any nested in it
        location_ids = [table_entry.id] + descendant_ids
        containers = Container.get_web_queryset().filter(location_id__in=location_ids)
        containers__count = containers.count()

        return {
            "location_path": table_entry.get_path(),
            "sub_locations__count": len(descendant_ids),
            "location_ids": location_ids,
            "containers": containers.order_by(
                # in-stock containers first (`is_depleted` is nullable)
                F("is_depleted").asc(nulls_first=True),
                "-id",
            )[:limit],
            "containers__count": containers__count,
            "containers__in_stock": containers.exclude(is_depleted=True).count(),
            "containers__truncated": containers__count > limit,
        }
