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
        "site",
        "building",
        "room",
        "lab",
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
