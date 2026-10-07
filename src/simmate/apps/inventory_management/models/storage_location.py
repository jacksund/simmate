# -*- coding: utf-8 -*-

from simmate.database.core import DatabaseTable, table_column


class StorageLocation(DatabaseTable):
    """
    A place where containers are stored, such as a room, cabinet, or freezer.

    Locations are hierarchical: each one can sit inside a `parent_location`
    (e.g. site > building > room > cabinet > shelf), which allows a container's
    full location to be traced.
    """

    class Meta:
        db_table = "inventory_management__storage_locations"

    # -------------------------------------------------------------------------

    name = table_column.CharField(max_length=255, blank=True, null=True)
    """
    A human-readable name for the location (e.g. "Freezer 2" or "Room 101").
    """

    storage_type_options = [
        "company",
        "school",
        "campus",
        "department",
        "site",
        "building",
        "room",
        "lab",
        "automated store",
        "fume hood",
        "glovebox",
        "cabinet",
        "flammables cabinet",
        "shelf",
        "drawer",
        "bench",
        "refrigerator",
        "freezer",
        "cold room",
        "desiccator",
        "box",
        "rack",
        "plate",
        "other",
    ]
    storage_type = table_column.CharField(
        max_length=30,
        blank=True,
        null=True,
    )
    """
    The kind of location this is. Must be one of `storage_type_options`.
    """

    temperature_celsius = table_column.IntegerField(
        default=20,
        blank=True,
        null=True,
    )
    """
    The temperature that the location is kept at, in degrees Celsius.
    Defaults to 20 (room temperature).
    """

    description = table_column.TextField(
        blank=True,
        null=True,
    )
    """
    Any extra details about the location (e.g. how to find or access it).
    """

    parent_location = table_column.ForeignKey(
        "self",
        on_delete=table_column.CASCADE,
        null=True,
        blank=True,
        related_name="sub_locations",
    )
    """
    The location that this one is inside of (e.g. the room that a cabinet is
    in). Deleting a location also deletes all of its sub-locations.
    """

    # -------------------------------------------------------------------------

    extra_metadata = table_column.JSONField(blank=True, null=True)
    """
    Any additional data about the location that does not fit in the columns
    above.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def get_or_create_path(
        cls,
        path: list[tuple[str, str | None]],
        cache: dict = None,
    ) -> int | None:
        """
        Gives the id of the last location in a path, creating any locations
        that don't exist yet. Gives None if the path is empty.

        The `path` is a list of `(name, storage_type)` pairs, from the top
        level down (e.g. `[("Building 1", "building"), ("Room 101", "room")]`).
        Locations are matched by their name and parent. The `storage_type` is
        only used when creating a location (existing ones are left as is).

        Pass the same `cache` dict to repeated calls (e.g. in a bulk load) so
        that each location is only looked up once.
        """
        if cache is None:
            cache = {}

        parent_id = None
        for name, storage_type in path:
            key = (parent_id, name)
            if key not in cache:
                location = cls.objects.filter(
                    parent_location_id=parent_id,
                    name=name,
                ).first() or cls.objects.create(
                    name=name,
                    storage_type=storage_type,
                    temperature_celsius=None,  # unknown
                    parent_location_id=parent_id,
                )
                cache[key] = location.id
            parent_id = cache[key]
        return parent_id
