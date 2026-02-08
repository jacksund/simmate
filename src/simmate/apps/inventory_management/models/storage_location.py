# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column


class StorageLocation(DatabaseTable):

    class Meta:
        db_table = "inventory_management__storage_locations"

    html_display_name = "Storage Locations"
    html_description_short = (
        "Specific areas where chemical containers are stored. Locations can be "
        "anything from an entire building to a specific cabinet. Locations "
        "can also have 'parent locations' to allow folder-like organization."
    )

    # -------------------------------------------------------------------------

    # disable cols
    source = None

    name = table_column.CharField(max_length=255, blank=True, null=True)

    temperature_celsius = table_column.IntegerField(
        default=20,
        blank=True,
        null=True,
    )

    description = table_column.TextField(
        blank=True,
        null=True,
    )

    parent_location = table_column.ForeignKey(
        "self",
        on_delete=table_column.CASCADE,
        null=True,
        blank=True,
        related_name="sub_locations",
    )
